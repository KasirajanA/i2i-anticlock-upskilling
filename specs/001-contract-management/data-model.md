# Data Model: Contract Management

## Entities

### Contract

| Column        | Type            | Constraints                                              |
|---------------|-----------------|----------------------------------------------------------|
| id            | INTEGER         | PK, autoincrement                                        |
| ref_id        | VARCHAR(10)     | UNIQUE NOT NULL — e.g., CON-0001                         |
| value         | DECIMAL(15,2)   | NOT NULL                                                 |
| start_date    | DATE            | NOT NULL                                                 |
| end_date      | DATE            | NOT NULL, CHECK(end_date >= start_date)                  |
| status        | VARCHAR(20)     | NOT NULL, DEFAULT 'Draft'                                |
| description   | TEXT            | NULLABLE                                                 |
| is_renewal_due| BOOLEAN         | NOT NULL DEFAULT FALSE                                   |
| is_archived   | BOOLEAN         | NOT NULL DEFAULT FALSE                                   |
| owner_id      | INTEGER         | FK → users.id NOT NULL                                   |
| account_id    | INTEGER         | FK → accounts.id NOT NULL                               |
| deal_id       | INTEGER         | FK → deals.id NULLABLE                                   |
| created_at    | DATETIME        | NOT NULL DEFAULT CURRENT_TIMESTAMP                       |
| updated_at    | DATETIME        | NOT NULL, updated on every write                         |

Valid status values: `Draft`, `Sent for Review`, `Active`, `Expired`, `Terminated`

---

### ContractAttachment

| Column       | Type        | Constraints                          |
|--------------|-------------|--------------------------------------|
| id           | INTEGER     | PK, autoincrement                    |
| contract_id  | INTEGER     | FK → contracts.id NOT NULL UNIQUE    |
| filename     | TEXT        | NOT NULL                             |
| mime_type    | TEXT        | NOT NULL                             |
| size_bytes   | INTEGER     | NOT NULL, CHECK(size_bytes <= 1048576) |
| storage_path | TEXT        | NOT NULL                             |
| created_at   | DATETIME    | NOT NULL DEFAULT CURRENT_TIMESTAMP   |

The UNIQUE constraint on `contract_id` enforces the one-attachment-per-contract rule at the DB layer.

---

### ActivityLog

| Column      | Type     | Constraints                        |
|-------------|----------|------------------------------------|
| id          | INTEGER  | PK, autoincrement                  |
| contract_id | INTEGER  | FK → contracts.id NOT NULL         |
| action_type | TEXT     | NOT NULL                           |
| actor_id    | INTEGER  | FK → users.id NOT NULL             |
| note        | TEXT     | NULLABLE (required for backward transitions, enforced at service layer) |
| created_at  | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP |

Typical `action_type` values: `status_transition`, `edit`, `attachment_added`, `attachment_removed`, `renewal_flagged`, `renewed`.

---

### RenewalLink

| Column                | Type     | Constraints                                   |
|-----------------------|----------|-----------------------------------------------|
| id                    | INTEGER  | PK, autoincrement                             |
| original_contract_id  | INTEGER  | FK → contracts.id NOT NULL                    |
| successor_contract_id | INTEGER  | FK → contracts.id NOT NULL UNIQUE             |
| created_at            | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP            |

The UNIQUE constraint on `successor_contract_id` ensures a successor contract cannot be linked to more than one original.

---

## Entity Relationship Map

```
users (existing)
  |
  |-- owns (owner_id) ----------> contracts
  |-- acts in (actor_id) -------> activity_logs
  |
accounts (existing)
  |
  +-- linked (account_id) ------> contracts
                                      |
deals (existing, nullable)            |--- 1:0..1 --> contract_attachments
  |                                   |
  +-- linked (deal_id) -------->      |--- 1:N --> activity_logs
                                      |
                                      |--- 1:0..1 (original) --> renewal_links
                                      |--- 1:0..1 (successor) -> renewal_links
```

---

## Index Recommendations

| Index Name                        | Table        | Columns                       | Reason                                          |
|-----------------------------------|--------------|-------------------------------|-------------------------------------------------|
| ix_contracts_status               | contracts    | status                        | Filter by status (SC-004)                       |
| ix_contracts_owner_id             | contracts    | owner_id                      | Filter by owner, access control                 |
| ix_contracts_account_id           | contracts    | account_id                    | Filter by account                               |
| ix_contracts_end_date             | contracts    | end_date                      | Date-range filter + nightly expiry job          |
| ix_contracts_status_end_date      | contracts    | status, end_date              | Composite: nightly renewal flagging query       |
| ix_contracts_is_archived          | contracts    | is_archived                   | Soft-delete exclusion on every list query       |
| ix_activity_logs_contract_id      | activity_logs| contract_id                   | Per-contract activity feed                      |
| ix_renewal_links_original_id      | renewal_links| original_contract_id          | Check if renewal exists before flagging         |

---

## Status State Machine

```
                    [Admin only, note required]
         +-----------------------------------------------+
         |                                               |
         v     forward only (all roles)                  |
   [Draft] --> [Sent for Review] --> [Active] --> [Expired]
                      |                  |
                      |                  +--> [Terminated]
                      |                            |
                      +----------------------------+
                      (Admin backward revert, note required)

  Daily job: Active contracts where end_date < today --> Expired (system actor)
  Daily job: Active contracts where end_date - today <= 30d AND no RenewalLink --> is_renewal_due = TRUE + notification
```

Forward transitions allowed per role:

| From              | To                  | Who              |
|-------------------|---------------------|------------------|
| Draft             | Sent for Review     | Sales Rep, Admin, Manager |
| Sent for Review   | Active              | Sales Rep (own), Admin, Manager |
| Active            | Expired             | System (auto) or Admin |
| Active            | Terminated          | Sales Rep (own), Admin, Manager |
| Any               | Any previous state  | Admin only (note required) |

---

## SQLAlchemy ORM Sketch: Contract

```python
from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, Enum,
    ForeignKey, Integer, Numeric, String, Text, UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ContractStatus(str, PyEnum):
    DRAFT = "Draft"
    SENT_FOR_REVIEW = "Sent for Review"
    ACTIVE = "Active"
    EXPIRED = "Expired"
    TERMINATED = "Terminated"


class Contract(Base):
    __tablename__ = "contracts"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_contracts_dates"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ref_id: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ContractStatus] = mapped_column(
        Enum(ContractStatus), nullable=False, default=ContractStatus.DRAFT
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_renewal_due: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    deal_id: Mapped[int | None] = mapped_column(ForeignKey("deals.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    attachment: Mapped["ContractAttachment | None"] = relationship(
        "ContractAttachment", back_populates="contract", uselist=False, cascade="all, delete-orphan"
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="contract", order_by="ActivityLog.created_at.desc()"
    )
    renewal_as_original: Mapped["RenewalLink | None"] = relationship(
        "RenewalLink", foreign_keys="RenewalLink.original_contract_id",
        back_populates="original_contract", uselist=False,
    )
    renewal_as_successor: Mapped["RenewalLink | None"] = relationship(
        "RenewalLink", foreign_keys="RenewalLink.successor_contract_id",
        back_populates="successor_contract", uselist=False,
    )
```
