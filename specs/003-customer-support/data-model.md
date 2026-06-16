# Data Model: Customer Support (Module 003)

**Date**: 2026-06-16 | **Feature**: 003-customer-support

---

## Entities

### Ticket

Primary support record.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | Internal key |
| `seq_number` | INTEGER | UNIQUE NOT NULL | Raw counter; formatted as `I2I-CRM-{seq_number:04d}` |
| `subject` | VARCHAR(255) | NOT NULL | |
| `description` | TEXT | | |
| `status` | VARCHAR(20) | NOT NULL, default `open` | `open` \| `in_progress` \| `resolved` \| `closed` |
| `priority` | VARCHAR(10) | NOT NULL | `low` \| `medium` \| `high` \| `critical` |
| `contact_id` | INTEGER | FK → contacts.id NULLABLE | NULL when contact is deleted |
| `contact_name_snapshot` | VARCHAR(255) | NOT NULL | Captured at ticket creation; preserved on contact delete |
| `account_id` | INTEGER | FK → accounts.id NULLABLE | Auto-filled from contact; nullable if account archived |
| `assignee_id` | INTEGER | FK → users.id NULLABLE | NULL = unassigned (shared queue) |
| `created_by_id` | INTEGER | FK → users.id NOT NULL | Agent who created the ticket |
| `created_at` | DATETIME | NOT NULL, default NOW | |
| `updated_at` | DATETIME | NOT NULL, default NOW | Updated on every change |
| `deleted_at` | DATETIME | NULLABLE | Soft-delete timestamp |

**Indexes**: `(status, created_at)`, `(assignee_id, status)`, `(contact_id)`, `(seq_number)`

---

### TicketSequence

Single-row counter for ticket ID generation.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | INTEGER | PK, always 1 |
| `next_value` | INTEGER | NOT NULL, default 1 |

---

### Reply

Thread entry on a ticket — customer-facing message or internal note.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `ticket_id` | INTEGER | FK → tickets.id NOT NULL | |
| `author_id` | INTEGER | FK → users.id NOT NULL | |
| `body` | TEXT | NOT NULL | |
| `is_internal` | BOOLEAN | NOT NULL, default FALSE | True = internal note (agents only) |
| `created_at` | DATETIME | NOT NULL, default NOW | |

**Indexes**: `(ticket_id, created_at)`

---

### SLARecord

Tracks SLA targets and actuals for one support cycle (original or re-open).

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `ticket_id` | INTEGER | FK → tickets.id NOT NULL | |
| `cycle` | INTEGER | NOT NULL, default 1 | Increments on each re-open |
| `first_response_due` | DATETIME | NOT NULL | Computed from `priority` SLA config at cycle start |
| `resolution_due` | DATETIME | NOT NULL | |
| `first_response_at` | DATETIME | NULLABLE | Set when first customer-facing reply is added |
| `resolved_at` | DATETIME | NULLABLE | Set when status moves to `resolved` |
| `first_response_breached` | BOOLEAN | NOT NULL, default FALSE | |
| `resolution_breached` | BOOLEAN | NOT NULL, default FALSE | |
| `is_active` | BOOLEAN | NOT NULL, default TRUE | FALSE for prior cycles after re-open |
| `created_at` | DATETIME | NOT NULL, default NOW | |

**Indexes**: `(ticket_id, is_active)`, `(first_response_due)`, `(resolution_due)`

---

### TicketActivityLog

Append-only audit trail for a ticket.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `ticket_id` | INTEGER | FK → tickets.id NOT NULL | |
| `event_type` | VARCHAR(30) | NOT NULL | See enum below |
| `actor_id` | INTEGER | FK → users.id NULLABLE | NULL for system events |
| `metadata` | JSON | | Event-specific payload |
| `created_at` | DATETIME | NOT NULL, default NOW | |

**`event_type` enum**: `status_change`, `assignment`, `reply_added`, `note_added`, `sla_breach`, `reopen`, `creation`, `contact_snapshot_preserved`

**Indexes**: `(ticket_id, created_at)`

---

## SLA Policy (in-code config, not a DB table)

```python
SLA_POLICY = {
    "critical": {"first_response_hours": 1,  "resolution_hours": 4},
    "high":     {"first_response_hours": 4,  "resolution_hours": 24},
    "medium":   {"first_response_hours": 8,  "resolution_hours": 48},
    "low":      {"first_response_hours": 24, "resolution_hours": 72},
}
```

---

## Relationships

```
Ticket ─── many ──► Reply
Ticket ─── many ──► SLARecord  (one active, zero or more inactive prior cycles)
Ticket ─── many ──► TicketActivityLog
Ticket ──── 1  ──► User (assignee, nullable)
Ticket ──── 1  ──► User (created_by)
Ticket ──── 1  ──► Contact (nullable; snapshot preserved)
Ticket ──── 1  ──► Account (nullable)
```

---

## State Machine

```
[Open] ──────────────────────────────► [In Progress]
  ▲                                          │
  │ (customer reply on Resolved ticket)      ▼
  └──────────────────────────── [Resolved] ──► [Closed]

Admin may revert any transition.
Agent may only advance: Open → In Progress → Resolved → Closed.
```

---

## Validation Rules

- `subject`: required, 1–255 characters
- `priority`: must be one of `low`, `medium`, `high`, `critical`
- `contact_id`: required at creation; nulled by system on contact deletion (snapshot preserved)
- `assignee_id`: optional at creation; must reference an active user with `role IN ('support_agent', 'admin')`
- `Reply.body`: required, 1–10,000 characters
- Status transitions enforced in `TicketService`; invalid transitions return HTTP 422
