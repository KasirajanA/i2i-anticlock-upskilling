# Research: Customer Support (Module 003)

**Date**: 2026-06-16 | **Feature**: 003-customer-support

---

## 1. Ticket ID Generation

**Decision**: Database-sequence-backed counter stored in a dedicated `ticket_sequence` table, formatted as `I2I-CRM-{N:04d}` at read time.

**Rationale**: SQLite lacks native sequences; a single-row `ticket_sequence` table updated with `UPDATE … RETURNING` inside the same transaction as `INSERT INTO tickets` guarantees uniqueness under concurrent writes (SQLite WAL serialises writes). Formatting (`I2I-CRM-0001`) is applied in the Pydantic response schema, not the DB column, so sorting on the raw integer remains possible.

**Alternatives considered**: UUID primary key with separate display ID (flexible, but harder to reference verbally); application-level counter with Redis (adds external dependency, out of scope MVP).

---

## 2. SLA Clock & Breach Detection

**Decision**: APScheduler `AsyncScheduler` polling every 5 minutes; SLA targets stored in a `sla_policy` mapping keyed by `TicketPriority`.

**Rationale**: SLA breach must surface within 5 minutes (SC-002). A scheduler job queries `SELECT id FROM tickets WHERE status NOT IN ('resolved','closed') AND sla_records.first_response_at IS NULL AND sla_records.first_response_due < NOW()` (and equivalent for resolution), flags breached records, and publishes in-app notifications via `NotificationService.dispatch()`. Storing SLA targets as a simple config dict (not a DB table) keeps the MVP schema minimal; per-account SLAs are deferred.

**Alternatives considered**: Trigger-based breach detection (SQLite triggers are synchronous, not async-compatible); real-time event-driven check on every ticket update (would require distributed coordination at scale).

---

## 3. Ticket Activity Log

**Decision**: Append-only `ticket_activity_log` table with `event_type` enum and JSON `metadata` column.

**Rationale**: All status transitions, assignments, replies, and system events must be auditable (FR-004). A single polymorphic log table with an `event_type` enum (`status_change`, `assignment`, `reply`, `note`, `sla_breach`, `reopen`) and a `metadata` JSON field handles every event without schema migrations for new event types. Reads are always filtered by `ticket_id`, so a composite index `(ticket_id, created_at)` keeps queries fast.

**Alternatives considered**: Separate tables per event type (strict schema, migration-heavy); event sourcing (over-engineered for MVP scale).

---

## 4. Re-open on Customer Reply

**Decision**: Agent-initiated reply endpoint checks ticket status; if `Resolved`, transitions to `Open`, creates new `SLARecord`, and dispatches `ticket.reopened` notification.

**Rationale**: Customer replies are entered manually by agents in v1 (no email-to-ticket ingestion). The `POST /tickets/{id}/replies` endpoint is the single entry point; re-open logic lives in `TicketService.add_reply()`. The original `SLARecord` is preserved with `is_active=False`; a new `SLARecord` is created for the re-opened cycle. In-app notification to the assigned agent uses Module 8 `NotificationService`.

**Alternatives considered**: Separate `/reopen` endpoint (redundant for manual-entry v1); state machine library (adds dependency without proportional value at this scale).

---

## 5. Soft-Delete / Orphaned Ticket Handling

**Decision**: `tickets.deleted_at` nullable timestamp for archiving; agent deactivation triggers a background task to flag orphaned tickets and notify Admin.

**Rationale**: Tickets must never block contact deletion (FR-011); retaining a `contact_name_snapshot` text column preserves the audit trail. When an agent is deactivated (Module 6 event), a `BackgroundTask` runs `UPDATE tickets SET assignee_id=NULL WHERE assignee_id=:uid AND status NOT IN ('resolved','closed')` and dispatches orphan notifications to Admins. No hard deletes permitted.

**Alternatives considered**: Cascade delete on agent deactivation (destroys audit trail); polling job to detect orphans (acceptable fallback but event-driven is lower latency).

---

## 6. Async FastAPI Architecture

**Decision**: All route handlers `async def`; database access via `AsyncSession` (one per request, injected via `Depends`); background work via `BackgroundTasks` or APScheduler.

**Rationale**: FastAPI's dependency injection with `async_sessionmaker(expire_on_commit=False)` avoids implicit lazy-load I/O. `BackgroundTasks` handles fire-and-forget post-response work (notification dispatch, orphan check). APScheduler handles periodic jobs. All service methods are `async def` and `await` DB operations.

**Alternatives considered**: Synchronous SQLAlchemy (blocks the event loop under concurrent load); Celery worker (adds Redis/RabbitMQ dependency, out of scope).

---

## 7. Frontend State & List Performance

**Decision**: TanStack Query `useInfiniteQuery` for the ticket list (cursor-based pagination, 50 rows/page); optimistic UI updates for status transitions.

**Rationale**: Ticket queues can reach 1,000 open tickets (SC-003); server-side pagination with a cursor on `(status, created_at, id)` keeps queries O(log n). Optimistic updates on status change prevent flash of stale state. `useQuery` for ticket detail view with `staleTime: 30_000` reduces refetch noise on active tickets.

**Alternatives considered**: Full-table load with client-side filter (unacceptable at 1,000 records); Redux for ticket state (over-engineered; TanStack Query + local useState sufficient).
