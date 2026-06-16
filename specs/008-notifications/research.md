# Research: Notifications & Alerts (Module 008)

**Date**: 2026-06-16 | **Feature**: 008-notifications

---

## 1. SSE Endpoint Implementation

**Decision**: Use `EventSourceResponse` (from `sse-starlette`) with per-client `asyncio.Queue`.

**Rationale**: Native SSE semantics (correct `Content-Type`, keep-alive pings, `Last-Event-ID` header support). Each connected user gets their own `asyncio.Queue`; the `SSEManager` singleton maps `user_id → Set[Queue]` to support multiple tabs. On reconnect, `Last-Event-ID` is read from the request header and missed events are replayed from the DB. For MVP there is no Redis; in-process fan-out is sufficient for SQLite-scale loads (≤1,000 concurrent users).

**Alternatives considered**: Raw `StreamingResponse` (verbose, no keep-alive), WebSockets (bidirectional overhead unnecessary), Redis Pub/Sub (correct for multi-process but adds operational dependency outside MVP scope).

---

## 2. Async SQLite Driver

**Decision**: SQLAlchemy 2.x `create_async_engine("sqlite+aiosqlite://...")` + `AsyncSession` (one per request via `async_sessionmaker`).

**Rationale**: `aiosqlite` wraps SQLite in a dedicated thread so `await` calls never block the event loop. `AsyncSession` with `expire_on_commit=False` avoids implicit lazy-load I/O after commits. SQLAlchemy's `DeclarativeBase` gives ORM models, relationship loading, and migration compatibility (Alembic). `NullPool` is not required for single-process SQLite.

**Alternatives considered**: Raw `aiosqlite` (fine for small projects but loses ORM/migration tooling), synchronous SQLite with `run_in_executor` (blocks the thread pool).

---

## 3. Background Jobs — Scheduler

**Decision**: APScheduler 4.x with `AsyncScheduler` + `SQLiteJobStore` (same DB file).

**Rationale**: No external broker required. Jobs persist across restarts. Two scheduled jobs:
- **Nightly purge** (`cron`, 02:00): `DELETE FROM notifications WHERE created_at < NOW() - 30 days`.
- **Digest flush** (`interval`, 60 s): Collapse pending same-user/same-event-type windows of ≥10 queued items into a single `is_digest=True` notification.

APScheduler 4.x integrates with `asyncio` via `await scheduler.start()` in the FastAPI lifespan handler.

**Alternatives considered**: Celery-beat (requires Redis broker, overkill), plain `asyncio.create_task` loop (no persistence, no cron expression support), FastAPI `BackgroundTasks` (per-request scope, not periodic).

---

## 4. Notification Batching / Digest

**Decision**: DB-side grouping with a 60-second tumbling window via APScheduler flush job.

**Rationale**: When ≥10 `Notification` rows share the same `(user_id, event_type, source_record_type)` within a 60-second window and `is_digest=False`, the flush job replaces them with one row (`is_digest=True`, `digest_count=N`). This avoids in-memory state and is crash-safe. The SSE layer broadcasts a `notification.refresh` event after the flush so active clients re-fetch the count.

**Alternatives considered**: In-memory debounce queue (lost on crash, not multi-process safe), client-side grouping (doesn't reduce DB writes).

---

## 5. Admin Notification Rule Storage & Evaluation

**Decision**: Normalised columns (`filter_field`, `filter_operator`, `filter_value`) + in-process cache.

**Rationale**: Separate columns enable SQL indexing on `event_type` and `target_type`. At startup (and on any rule CRUD), all enabled rules are loaded into a `List[AdminNotificationRule]` held by `RuleEngine`. At event dispatch time, the engine filters in-process (sub-millisecond for ≤100 rules) — no DB round-trip. Single comparison operator (`>`, `<`, `=`, `>=`, `<=`, `in`) evaluated against event context dict.

**Alternatives considered**: JSON condition column (flexible but slower `json_extract` queries), DB table scan per event (acceptable ≤10 rules, degrades at 50+), Redis rule cache (unnecessary external dep).

---

## 6. React State Management for Notifications

**Decision**: React Context + `useReducer` for local notification state; TanStack Query (`useInfiniteQuery`) for paginated list; SSE events trigger context dispatch + query invalidation.

**Rationale**: Context + `useReducer` handles real-time add/read/clear actions cleanly without a third-party store. TanStack Query manages server-cache for the infinite-scroll list (cursor-based pagination) and badge count refetch. SSE custom hook (`useEventSource`) dispatches to context on `notification.new` and `notification.refresh` events.

**Alternatives considered**: Zustand (simpler API but adds dependency), Redux (over-engineered for single module), polling (defeats SSE latency goal).

---

## 7. UI Component Library

**Decision**: **MUI (Material UI) v6** with custom CRM theme.

**Rationale**: Comprehensive enterprise-grade components (Badge, Menu, List, IconButton, Drawer, Switch for preferences). Built-in WCAG 2.1 AA compliance. Excellent TypeScript support. `sx` prop + `createTheme` for brand customisation. Ships `DataGrid` for future report modules. Widely adopted in CRM products.

**Alternatives considered**: Tailwind + shadcn/ui (maximum control, but requires composing accessibility primitives manually), Ant Design (strong but heavier, Chinese-market aesthetic by default).

---

## 8. Accessibility (WCAG 2.1 AA)

**Decision**: `aria-live="polite"` region for new notification announcements; `aria-label` on bell button with live count; focus trap + `Escape` to close panel; full keyboard navigation.

**Rationale**: MUI `Menu`/`Popover` ships with Radix-based focus management. `aria-live` region outside the bell button ensures screen readers announce "3 new notifications" without interrupting current speech. `role="status"` badge for count update.

---

## 9. Testing Stack

**Decision**: **pytest + pytest-asyncio** (backend), **Vitest + React Testing Library** (frontend).

**Rationale**: `pytest-asyncio` supports `async def test_*` natively with `aiosqlite`. Vitest is fast (Vite-native) and shares config with the React build. React Testing Library enforces accessible queries (`getByRole`, `getByLabelText`) aligning with WCAG goals.

**Alternatives considered**: `unittest` (verbose), Jest (works but slower than Vitest for Vite projects).
