# Data Model: Notifications & Alerts (Module 008)

**Date**: 2026-06-16 | **Storage**: SQLite via SQLAlchemy 2.x + aiosqlite

---

## Entity Map

```
User (Module 005)
 └─< Notification          (one user → many notifications)
 └─< NotificationPreference (one user → many preferences, one per event type)
 └─< AdminNotificationRule  (created_by FK)

AdminNotificationRule
 └─< Notification           (optional back-ref: admin_rule_id)
```

---

## Entities

### Notification

Core delivery record — one row per user per event instance (or one digest row).

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK AUTOINCREMENT | |
| `user_id` | INTEGER | FK → `users.id` NOT NULL | Recipient |
| `event_type` | TEXT | NOT NULL | Enum — see below |
| `title` | TEXT | NOT NULL | Display text, max 200 chars |
| `body` | TEXT | | Optional detail text |
| `source_record_type` | TEXT | | `deal`, `ticket`, `contract`, `contact` |
| `source_record_id` | INTEGER | | FK-like, soft reference (no cascade) |
| `is_read` | BOOLEAN | NOT NULL DEFAULT FALSE | |
| `is_digest` | BOOLEAN | NOT NULL DEFAULT FALSE | TRUE when batched |
| `digest_count` | INTEGER | NOT NULL DEFAULT 1 | >1 for digest rows |
| `admin_rule_id` | INTEGER | FK → `admin_notification_rules.id` NULLABLE | NULL if user-pref triggered |
| `created_at` | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | |
| `expires_at` | DATETIME | NOT NULL | `created_at + 30 days`; purge job uses this |

**Indexes**: `(user_id, is_read, created_at DESC)`, `(expires_at)` (purge query), `(user_id, event_type, source_record_type, created_at)` (digest flush query).

**Event type enum** (stored as TEXT):
```
assignment | comment | mention | status_change |
contract_renewal_due | deal_stage_change | sla_breach
```

**State transitions**:
```
created (is_read=False) → read (is_read=True)
                        → purged (deleted by nightly job when expires_at < NOW())
```

---

### NotificationPreference

Per-user toggle for each event type. All event types default ON if no row exists (application-level default).

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK AUTOINCREMENT | |
| `user_id` | INTEGER | FK → `users.id` NOT NULL | |
| `event_type` | TEXT | NOT NULL | Same enum as Notification |
| `is_enabled` | BOOLEAN | NOT NULL DEFAULT TRUE | |
| `updated_at` | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | |

**Unique constraint**: `(user_id, event_type)` — upsert on preference save.

**Application logic**: Before creating a Notification, check `NotificationPreference` for the recipient. If no row exists, treat as `is_enabled=TRUE`. Admin-rule-triggered notifications bypass this check (FR-004).

---

### AdminNotificationRule

Organisation-wide rules configured by Admins. Evaluated in-process on every event dispatch.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK AUTOINCREMENT | |
| `name` | TEXT | NOT NULL | Human label, max 100 chars |
| `event_type` | TEXT | NOT NULL | Same enum as Notification |
| `filter_field` | TEXT | NULLABLE | e.g., `deal_value`, `priority`, `status` |
| `filter_operator` | TEXT | NULLABLE | `>` `<` `=` `>=` `<=` `in` |
| `filter_value` | TEXT | NULLABLE | Stored as string; cast at eval time |
| `target_type` | TEXT | NOT NULL | `role` or `user` |
| `target_value` | TEXT | NOT NULL | Role name (`Admin`, etc.) or user `id` as string |
| `is_enabled` | BOOLEAN | NOT NULL DEFAULT TRUE | |
| `created_by` | INTEGER | FK → `users.id` NOT NULL | |
| `created_at` | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | |
| `updated_at` | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | |

**Indexes**: `(event_type, is_enabled)` for cache reload query.

**Validation rules**:
- `filter_field`, `filter_operator`, `filter_value` must all be NULL or all be non-NULL.
- `filter_operator` must be one of: `>`, `<`, `=`, `>=`, `<=`, `in`.
- `target_type` = `role` → `target_value` ∈ {`Admin`, `Manager`, `Sales Rep`, `Support Agent`}.
- `target_type` = `user` → `target_value` must parse as a valid integer user ID.

---

## SQLAlchemy ORM Class Sketch

```python
# app/models/notification.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Index, text
from datetime import datetime
from enum import StrEnum

class EventType(StrEnum):
    ASSIGNMENT = "assignment"
    COMMENT = "comment"
    MENTION = "mention"
    STATUS_CHANGE = "status_change"
    CONTRACT_RENEWAL_DUE = "contract_renewal_due"
    DEAL_STAGE_CHANGE = "deal_stage_change"
    SLA_BREACH = "sla_breach"

class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    body: Mapped[str | None]
    source_record_type: Mapped[str | None]
    source_record_id: Mapped[int | None]
    is_read: Mapped[bool] = mapped_column(default=False)
    is_digest: Mapped[bool] = mapped_column(default=False)
    digest_count: Mapped[int] = mapped_column(default=1)
    admin_rule_id: Mapped[int | None] = mapped_column(ForeignKey("admin_notification_rules.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=text("CURRENT_TIMESTAMP"))
    expires_at: Mapped[datetime] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_notif_user_read_created", "user_id", "is_read", "created_at"),
        Index("ix_notif_expires", "expires_at"),
        Index("ix_notif_digest_window", "user_id", "event_type", "source_record_type", "created_at"),
    )
```

---

## Migration Notes

- `expires_at` is computed at insert time: `datetime.utcnow() + timedelta(days=30)`.
- No FK cascade on `source_record_id` — notifications survive record soft-deletes.
- `admin_rule_id` FK has `ON DELETE SET NULL` so deleting a rule does not remove past notifications.
- All tables created via `Base.metadata.create_all(engine)` for MVP; Alembic migrations added before production.
