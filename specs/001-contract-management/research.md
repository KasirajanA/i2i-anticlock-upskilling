# Research: Contract Management

## Decision 1: Async SQLite Driver — SQLAlchemy 2.x + aiosqlite

**Decision**: Use SQLAlchemy 2.x async engine with `aiosqlite` as the driver (`sqlite+aiosqlite://`).

**Rationale**: FastAPI is built on ASGI and `asyncio`; a synchronous DB driver would block the event loop under concurrent requests, degrading p95 latency. SQLAlchemy 2.x async mode wraps `aiosqlite` transparently, so the ORM API stays consistent. WAL mode (enabled on the SQLite file) allows concurrent readers alongside a single writer, satisfying SC-004 (sub-1s filtered list for 10k rows) without a heavier RDBMS.

**Alternatives**:
- **Databases (encode/databases)**: lightweight but lacks full ORM; would require raw SQL for relationship traversal and complex joins across Contract, ActivityLog, and RenewalLink.
- **SQLAlchemy sync + threadpool**: `run_in_executor` workaround is brittle; every async handler must wrap calls, increasing cyclomatic complexity.

---

## Decision 2: File Attachment Storage — Local Disk MVP

**Decision**: Store attachment files under `backend/attachments/{contract_id}/` and serve them via FastAPI `FileResponse`. Metadata (filename, MIME type, size, path) is persisted in `ContractAttachment`.

**Rationale**: For an MVP with a 1 MB per-file cap and a single-server deployment, local disk eliminates infrastructure dependencies (no S3, no MinIO). FastAPI's `FileResponse` streams the file efficiently. The `storage_path` column in `ContractAttachment` makes a future migration to object storage a one-column update with no API contract change.

**Alternatives**:
- **MinIO / S3-compatible**: operationally correct long-term but adds a containerised dependency and IAM configuration that slows MVP delivery.
- **Store binary in SQLite BLOB**: breaches separation of concerns and inflates the DB file; queries on contract metadata become slower as BLOB rows grow.

---

## Decision 3: Testing Stack — pytest-asyncio + httpx (backend), Vitest + RTL (frontend)

**Decision**: Backend tests use `pytest` with `pytest-asyncio` and `httpx.AsyncClient` against a real in-process app; frontend tests use `Vitest` with React Testing Library.

**Rationale**: `pytest-asyncio` handles `async def` test coroutines natively, letting integration tests call the live FastAPI app via `httpx.AsyncClient` without a running server process. This exercises actual SQL queries against an in-memory SQLite instance, catching ORM mapping and migration issues early. On the frontend, Vitest shares Vite config so TypeScript aliases and module resolution are identical to production; RTL enforces user-centric assertions over implementation details.

**Alternatives**:
- **pytest + requests (sync)**: requires `TestClient` (sync transport), which blocks the event loop and cannot test `asyncio` background job interactions.
- **Jest (frontend)**: heavier configuration for a Vite project; no shared config with the build toolchain.
