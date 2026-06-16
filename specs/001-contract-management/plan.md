# Implementation Plan: Contract Management

**Branch**: `001-contract-management` | **Date**: 2026-06-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-contract-management/spec.md`

---

## Summary

This module enables Sales Reps and Admins to create, manage, and track contracts linked to accounts and deals, with full lifecycle management (Draft → Sent for Review → Active → Expired/Terminated), file attachment support, and automated renewal tracking. The implementation uses FastAPI with async SQLAlchemy over SQLite (WAL mode), an APScheduler nightly job for auto-expiry and renewal flagging, and a React + MUI frontend consuming a versioned REST API.

---

## Technical Context

**Language/Version**: Python 3.14 (backend), TypeScript 5 (frontend)

**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.x async (aiosqlite), APScheduler 4.x AsyncScheduler, Uvicorn (backend); React 18, MUI v6, TanStack Query v5, Vite (frontend)

**Storage**: SQLite WAL mode — single file `crm.db`; file attachments on local disk under `backend/attachments/{contract_id}/`

**Testing**: pytest + pytest-asyncio + httpx.AsyncClient (backend); Vitest + React Testing Library (frontend)

**Target Platform**: Linux server (single-process, ASGI)

**Project Type**: Full-stack web application (REST API + SPA)

**Performance Goals**:
- SC-001: Contract creation UX completes in < 2 minutes
- SC-002: Auto-expiry job runs within 24 hours of end_date passing
- SC-003: Renewal Due flag set within 24 hours of entering 30-day window
- SC-004: Filtered list API p95 < 1s for 10,000 contracts
- SC-006: File upload < 2s for 1 MB payload

**Constraints**: API p95 ≤ 200ms (constitution NFR); cyclomatic complexity ≤ 10 per function; backward compatibility with existing `users`, `accounts`, `deals` tables; no hard deletes (soft-delete via `is_archived`); file size cap 1 MB enforced at API layer

**Scale/Scope**: Up to 10,000 contract records; single-tenant MVP; 4 fixed roles (Admin, Manager, Sales Rep, Support Agent — Support Agent has no access to this module)

---

## Constitution Check

| Principle                         | Status | Evidence                                                                                  |
|-----------------------------------|--------|-------------------------------------------------------------------------------------------|
| API p95 ≤ 200ms                   | PASS   | Indexed queries on status, owner_id, account_id, end_date; SQLite WAL; paginated list (max 100 per page) |
| Page load ≤ 2s                    | PASS   | TanStack Query caching; paginated API response; MUI skeleton loaders during fetch         |
| Cyclomatic complexity ≤ 10        | PASS   | Transition logic isolated in `ContractService.transition()`; state machine table replaces nested conditionals |
| Soft-delete only (no hard delete) | PASS   | `is_archived` flag on Contract; `DELETE /attachment` removes file + metadata but contract record is retained |
| HIPAA / data privacy              | PASS   | No PHI in this module; contract data is commercial; session auth enforces access control; no external data egress |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-contract-management/
├── plan.md                     # This file
├── spec.md                     # Feature specification
├── research.md                 # Phase 0 decisions
├── data-model.md               # Entity schemas, ERD, ORM sketch
├── quickstart.md               # Setup + validation scenarios
├── contracts/
│   └── api.md                  # Full REST API contract
└── tasks.md                    # Phase 2 output (speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                             # FastAPI app factory, router registration
│   ├── core/
│   │   ├── config.py                       # Settings (DB URL, attachment path, etc.)
│   │   ├── database.py                     # Async engine, session factory
│   │   └── security.py                     # Session auth, role guard helpers
│   ├── models/
│   │   └── contracts.py                    # Contract, ContractAttachment, ActivityLog, RenewalLink ORM models
│   ├── schemas/
│   │   └── contracts.py                    # Pydantic v2 request/response schemas
│   ├── repositories/
│   │   └── contract_repository.py          # Async CRUD + filter queries
│   ├── services/
│   │   └── contract_service.py             # Business logic: transitions, renewal, attachment replace
│   ├── scheduler/
│   │   └── jobs.py                         # APScheduler jobs: expire_contracts, flag_renewals
│   └── api/
│       └── v1/
│           ├── __init__.py
│           └── contracts.py                # All /api/v1/contracts route handlers
├── attachments/                            # Runtime: {contract_id}/filename stored here (gitignored)
├── alembic/
│   └── versions/
│       └── 001_create_contracts_tables.py  # Migration: contracts, attachments, activity_logs, renewal_links
├── tests/
│   ├── unit/
│   │   ├── test_contract_service.py        # Transition logic, renewal date calculation, attachment replace
│   │   └── test_contract_schemas.py        # Pydantic validation edge cases
│   └── integration/
│       ├── test_contracts_api.py           # Full CRUD + transition + renew + attachment endpoints
│       └── test_scheduler_jobs.py          # Auto-expiry and renewal flagging jobs
└── requirements.txt

frontend/
├── src/
│   ├── types/
│   │   └── contracts.ts                    # Contract, ContractAttachment, ActivityLog, RenewalLink TS types
│   ├── services/
│   │   └── contractsApi.ts                 # Axios/fetch wrappers for all /api/v1/contracts endpoints
│   ├── hooks/
│   │   └── useContracts.ts                 # TanStack Query hooks: useContracts, useContract, useMutateContract
│   ├── components/
│   │   └── contracts/
│   │       ├── ContractList.tsx            # Filterable paginated list with Renewal Due badge
│   │       ├── ContractForm.tsx            # Create/edit form with validation
│   │       ├── ContractDetail.tsx          # Detail view: fields + attachment + activity log
│   │       ├── ContractStatusChip.tsx      # Status badge with colour mapping
│   │       ├── ContractTransitionDialog.tsx# Status transition modal with optional note
│   │       ├── ContractAttachmentPanel.tsx # Upload/replace/delete attachment widget
│   │       └── ContractActivityLog.tsx     # Timeline of activity log entries
│   ├── pages/
│   │   ├── ContractsPage.tsx               # Route: /contracts
│   │   └── ContractDetailPage.tsx          # Route: /contracts/:refId
│   └── store/
│       └── notificationStore.ts            # In-app notification state (Renewal Due alerts)
└── tests/
    ├── ContractList.test.tsx
    ├── ContractForm.test.tsx
    └── ContractDetail.test.tsx
```

**Structure Decision**: Web application layout (Option 2) — separate `backend/` and `frontend/` trees. All contract-specific source files are new; shared infrastructure files (`core/`, `main.py`) are extended, not replaced.

---

## Complexity Tracking

No violations.

---

## Key Design Decisions

### 1. Status Machine as a Data-Driven Table

The valid transition map is declared as a dictionary constant in `contract_service.py` rather than a chain of if/elif blocks. Each key is a `(from_status, role)` tuple and the value is the set of permitted target statuses. This keeps cyclomatic complexity of the transition method at or below 5, makes adding future states a one-line change, and produces clear `400` errors with no hidden control paths.

**Rationale**: A naive if/elif approach across 5 statuses × 4 roles produces cyclomatic complexity > 10, violating the constitution NFR.

### 2. Attachment Replace-in-Place via Atomic DB + Disk Operations

When a new file is uploaded to a contract that already has an attachment, the service: (1) deletes the old file from disk, (2) removes the old `ContractAttachment` row, (3) writes the new file, (4) inserts the new `ContractAttachment` row — all within a single SQLAlchemy async transaction. If the disk write fails after the DB delete, the transaction is rolled back and the old metadata record is restored (though the old file is already gone; the contract attachment will be `null` until re-uploaded). This trade-off is acceptable for an MVP with local disk storage.

**Rationale**: The UNIQUE constraint on `ContractAttachment.contract_id` prevents duplicate rows, and the transaction boundary ensures the DB never points to a non-existent file path.

### 3. APScheduler Jobs with Internal Trigger Endpoints

The nightly expiry and renewal-flagging jobs are registered with APScheduler's `AsyncScheduler` at app startup. For testability and manual operations, each job is also exposed as a POST endpoint under `/api/v1/internal/jobs/` (Admin-only). This avoids time-mocking complexity in integration tests and allows on-demand execution during the validation scenarios in `quickstart.md`.

**Rationale**: Waiting 24 hours to verify SC-002 and SC-003 in CI is impractical; the internal trigger endpoints let tests invoke the exact same job function that runs on the cron schedule.
