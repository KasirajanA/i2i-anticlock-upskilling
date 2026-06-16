# Research: Sales Pipeline

**Module**: 002 - Sales Pipeline
**Date**: 2026-06-16

---

## Decision 1: Async SQLite Driver — SQLAlchemy 2.x + aiosqlite

**Decision**: Use SQLAlchemy 2.x async engine with `aiosqlite` as the async SQLite driver, configured in WAL mode.

**Rationale**: SQLAlchemy 2.x's async API (`AsyncSession`, `AsyncEngine`) integrates cleanly with FastAPI's async request lifecycle, preventing event-loop blocking on I/O. WAL mode allows concurrent readers without blocking the APScheduler background writer. The ORM layer keeps model definitions consistent across all modules and allows query composition without raw SQL.

**Alternatives**:
- `encode/databases` with raw queries: lighter weight, but no ORM abstractions and no shared model layer across modules.
- Synchronous SQLAlchemy in a thread-pool: works but adds thread overhead and obscures concurrency boundaries.

---

## Decision 2: Stage Transition Model and Overdue Detection

**Decision**: Implement stages as a Python `StrEnum`. Transitions are free-flow except that `Closed Won` and `Closed Lost` are terminal — the service layer raises `HTTP 422` on any further stage change. Overdue detection uses an APScheduler `AsyncScheduler` cron job that runs daily at 01:00 UTC, sets `is_overdue=True` on deals where `expected_close_date < today` and stage is not a closed stage, and clears the flag when a deal advances to `Closed Won` or `Closed Lost`. Notifications are inserted into the existing notifications table in the same transaction.

**Rationale**: Free-flow transitions avoid encoding a rigid sequence in the DB while still enforcing the terminal constraint in one place. A daily job is sufficient for the SLA (FR-011 says "close date passes") and avoids per-request overhead. Flag-plus-reset keeps the query for the board filter (`is_overdue=true`) a simple indexed column lookup.

**Alternatives**:
- Transition matrix (allowable-next-stage table): flexible but over-engineered for a fixed 6-stage pipeline in v1.
- Computed overdue column (no flag): requires a function-based index on SQLite; portability concern and harder to drive notifications from.

---

## Decision 3: Testing Stack — pytest-asyncio + httpx (backend), Vitest + RTL (frontend)

**Decision**: Backend tests use `pytest-asyncio` with `anyio` mode, `httpx.AsyncClient` against the FastAPI `app`, and an in-memory SQLite database seeded per test. Frontend tests use Vitest with React Testing Library and `msw` for API mocking.

**Rationale**: `pytest-asyncio` handles `async def` test functions natively; `httpx.AsyncClient` drives the ASGI app without spinning up a real server, giving fast integration tests. Vitest shares the same Vite config as the app, reducing toolchain duplication; RTL encourages testing user-visible behaviour over implementation details.

**Alternatives**:
- `unittest + requests` + synchronous test client: works but forces sync wrappers around async DB fixtures.
- Jest instead of Vitest: more mature ecosystem but separate config and slower cold starts when Vite is already in use.
