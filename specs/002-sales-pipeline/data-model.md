# Data Model: Sales Pipeline

**Module**: 002 - Sales Pipeline
**Date**: 2026-06-16

---

## Entities

### Deal

| Column              | Type              | Constraints                                                  |
|---------------------|-------------------|--------------------------------------------------------------|
| id                  | INTEGER           | PK, autoincrement                                            |
| ref_id              | VARCHAR(12)       | UNIQUE NOT NULL — format `DEAL-NNNN`, generated on insert    |
| title               | TEXT              | NOT NULL                                                     |
| value               | DECIMAL(15, 2)    | NOT NULL DEFAULT 0.00                                        |
| stage               | VARCHAR(20)       | NOT NULL, CHECK in stage enum                                |
| expected_close_date | DATE              | NOT NULL                                                     |
| owner_id            | INTEGER           | FK → users.id NOT NULL                                       |
| account_id          | INTEGER           | FK → contacts.accounts.id NULLABLE                           |
| contact_id          | INTEGER           | FK → contacts.contacts.id NULLABLE                           |
| loss_reason         | TEXT              | NULLABLE — required when stage = Closed Lost                 |
| is_overdue          | BOOLEAN           | NOT NULL DEFAULT FALSE                                       |
| is_archived         | BOOLEAN           | NOT NULL DEFAULT FALSE                                       |
| created_at          | DATETIME          | NOT NULL DEFAULT CURRENT_TIMESTAMP                           |
| updated_at          | DATETIME          | NOT NULL, updated via ORM event                              |

### DealComment

| Column     | Type     | Constraints                        |
|------------|----------|------------------------------------|
| id         | INTEGER  | PK, autoincrement                  |
| deal_id    | INTEGER  | FK → deals.id NOT NULL             |
| author_id  | INTEGER  | FK → users.id NOT NULL             |
| body       | TEXT     | NOT NULL                           |
| is_deleted | BOOLEAN  | NOT NULL DEFAULT FALSE (soft delete)|
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP |

### ActivityLog

| Column      | Type     | Constraints                              |
|-------------|----------|------------------------------------------|
| id          | INTEGER  | PK, autoincrement                        |
| deal_id     | INTEGER  | FK → deals.id NOT NULL                   |
| action_type | VARCHAR(40) | NOT NULL — see action type list below |
| actor_id    | INTEGER  | FK → users.id NOT NULL                   |
| note        | TEXT     | NULLABLE                                 |
| created_at  | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP       |

**action_type values**: `stage_changed`, `field_updated`, `comment_added`, `comment_deleted`, `deal_created`, `deal_archived`, `overdue_flagged`, `assigned`

---

## Entity Relationship Map

```
users
  |
  |  owner_id                  actor_id / author_id
  +------------------+  +-------------------------------+
  |                  |  |                               |
  v                  v  v                               |
deals <----------> activity_log                         |
  |    deal_id                                          |
  |                                                     |
  +---> deal_comments <-------- (author_id) ------------+
  |       deal_id
  |
  +---> contacts.accounts   (account_id, nullable)
  |
  +---> contacts.contacts   (contact_id, nullable)
```

---

## Index Recommendations

| Index Name                        | Table        | Columns                                  | Reason                                          |
|-----------------------------------|--------------|------------------------------------------|-------------------------------------------------|
| idx_deals_owner_stage             | deals        | (owner_id, stage)                        | Pipeline board filtered by owner + stage        |
| idx_deals_stage                   | deals        | (stage)                                  | Forecast grouping by stage                      |
| idx_deals_expected_close_date     | deals        | (expected_close_date)                    | Overdue job and forecast period filter          |
| idx_deals_is_overdue              | deals        | (is_overdue)                             | Board/list overdue filter                       |
| idx_deals_account_id              | deals        | (account_id)                             | Filter by account                               |
| idx_deals_ref_id                  | deals        | (ref_id) UNIQUE                          | Direct lookup by reference ID                   |
| idx_activity_log_deal_id          | activity_log | (deal_id)                                | Fetch all events for a deal                     |
| idx_deal_comments_deal_id         | deal_comments| (deal_id)                                | Fetch comments for a deal                       |

---

## Stage State Machine

```
Lead In ──────────────────────────────────────────────────────> Closed Won (terminal)
   |                                                                  ^
   v                                                                  |
Qualified ────────────────────────────────────────────────────> Closed Won (terminal)
   |                                                                  ^
   v                                                                  |
Proposal ─────────────────────────────────────────────────────> Closed Won (terminal)
   |                                                                  ^
   v                                                                  |
Negotiation ──────────────────────────────────────────────────> Closed Won (terminal)
   |
   v
Closed Lost (terminal)

Rules:
- Any non-closed stage can transition to any other non-closed stage (free-flow).
- Any non-closed stage can transition directly to Closed Won or Closed Lost.
- Closed Won and Closed Lost are TERMINAL — no further stage changes permitted.
- Transitioning to Closed Lost REQUIRES a loss_reason in the request body.
- is_overdue is cleared atomically when a deal transitions to Closed Won or Closed Lost.
```

---

## SQLAlchemy ORM Class Sketch — Deal

```python
import enum
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (
    Boolean, Date, DateTime, Enum, ForeignKey,
    Integer, Numeric, String, Text, event, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DealStage(str, enum.Enum):
    LEAD_IN      = "Lead In"
    QUALIFIED    = "Qualified"
    PROPOSAL     = "Proposal"
    NEGOTIATION  = "Negotiation"
    CLOSED_WON   = "Closed Won"
    CLOSED_LOST  = "Closed Lost"

    @property
    def is_terminal(self) -> bool:
        return self in (DealStage.CLOSED_WON, DealStage.CLOSED_LOST)

    @classmethod
    def probability(cls, stage: "DealStage") -> float:
        return {
            cls.LEAD_IN:     0.10,
            cls.QUALIFIED:   0.25,
            cls.PROPOSAL:    0.50,
            cls.NEGOTIATION: 0.75,
            cls.CLOSED_WON:  1.00,
            cls.CLOSED_LOST: 0.00,
        }[stage]


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[int]             = mapped_column(Integer, primary_key=True)
    ref_id: Mapped[str]         = mapped_column(String(12), unique=True, nullable=False)
    title: Mapped[str]          = mapped_column(Text, nullable=False)
    value: Mapped[Decimal]      = mapped_column(Numeric(15, 2), nullable=False, default=0)
    stage: Mapped[DealStage]    = mapped_column(Enum(DealStage), nullable=False)
    expected_close_date: Mapped[date] = mapped_column(Date, nullable=False)
    owner_id: Mapped[int]       = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    account_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=True)
    contact_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("contacts.id"), nullable=True)
    loss_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_overdue: Mapped[bool]    = mapped_column(Boolean, nullable=False, default=False)
    is_archived: Mapped[bool]   = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    owner       = relationship("User", foreign_keys=[owner_id])
    account     = relationship("Account", foreign_keys=[account_id])
    contact     = relationship("Contact", foreign_keys=[contact_id])
    comments    = relationship("DealComment", back_populates="deal", lazy="select")
    activity    = relationship("ActivityLog",  back_populates="deal", order_by="ActivityLog.created_at")
```
