# Tasks: Contract Management

**Feature Branch**: `001-contract-management`
**Input**: Design documents from `specs/001-contract-management/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/api.md ✅, quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[US#]**: Maps to user story from spec.md
- Each task includes exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project skeleton per plan.md structure

- [X] T001 Create backend directory structure: `backend/app/{core,models,schemas,repositories,services,scheduler,api/v1}`, `backend/tests/{unit,integration}`, `backend/alembic/versions`, `backend/scripts`, `backend/attachments/`
- [X] T002 [P] Create frontend directory structure: `frontend/src/{types,services,hooks,components/contracts,pages,store}`, `frontend/tests/`
- [X] T003 [P] Create `backend/requirements.txt` with FastAPI, Pydantic v2, SQLAlchemy 2.x, aiosqlite, APScheduler 4.x, Uvicorn, Alembic, python-multipart, pytest, pytest-asyncio, httpx, ruff
- [X] T004 [P] Initialize `frontend/package.json` and `frontend/vite.config.ts` with React 18, MUI v6, TanStack Query v5, Vite, Vitest, React Testing Library, TypeScript 5

**Checkpoint**: Project skeleton ready — dependency installation can begin

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, schemas, repository, and security layer — MUST be complete before any user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create Alembic migration `backend/alembic/versions/001_create_contracts_tables.py` for `contracts`, `contract_attachments`, `activity_logs`, `renewal_links` tables including all FK constraints, CHECK constraints (`ck_contracts_dates`, `size_bytes ≤ 1 048 576`), UNIQUE constraints, and all eight indexes from data-model.md
- [X] T006 Define `ContractStatus` enum and `Contract` ORM model (all columns, `CheckConstraint`, relationships to attachment/activity_logs/renewal links) in `backend/app/models/contracts.py`
- [X] T007 Add `ContractAttachment`, `ActivityLog`, and `RenewalLink` ORM models (with back-populates) to `backend/app/models/contracts.py`
- [X] T008 [P] Create all Pydantic v2 request/response schemas (`ContractCreate`, `ContractUpdate`, `ContractResponse`, `ContractListResponse`, `TransitionRequest`, `TransitionResponse`, `AttachmentResponse`, `ActivityLogEntry`, `ActivityLogResponse`, `RenewResponse`) in `backend/app/schemas/contracts.py`
- [X] T009 [P] Implement `ContractRepository` with async session-scoped methods: `create`, `get_by_ref_id`, `update`, `list_paginated`, `get_next_seq` (for CON-NNNN generation) in `backend/app/repositories/contract_repository.py`
- [X] T010 [P] Extend `backend/app/core/security.py` with `require_roles(*roles)` FastAPI dependency and `assert_contract_ownership(contract, current_user)` helper
- [X] T011 [P] Create TypeScript types `Contract`, `ContractAttachment`, `ActivityLog`, `RenewalLink`, `ContractStatus`, `ContractListResponse`, `TransitionRequest`, `RenewResponse` in `frontend/src/types/contracts.ts`
- [X] T012 Create `ContractService` base class with async session dependency injection in `backend/app/services/contract_service.py`
- [X] T013 Create `backend/app/api/v1/__init__.py` and skeleton `contracts.py` `APIRouter`; register router under `/api/v1` prefix in `backend/app/main.py`

**Checkpoint**: Foundation ready — all four user stories can now be implemented in parallel

---

## Phase 3: User Story 1 — Create a Contract (Priority: P1) 🎯 MVP

**Goal**: Sales Rep can create a contract with CON-NNNN ref_id, attach a file, edit draft fields, and view the contract detail page.

**Independent Test**: `POST /api/v1/contracts` with valid `account_id`, `value`, `start_date`, `end_date` returns 201 with `status: "Draft"` and `ref_id: "CON-0001"`; contract visible via `GET /api/v1/contracts/{ref_id}` with attachment `null`.

- [X] T014 [US1] Implement CON-NNNN ref_id auto-generation (zero-padded sequential counter via `get_next_seq`) in `backend/app/services/contract_service.py`
- [X] T015 [US1] Implement `ContractService.create()` persisting contract row and initial `status_transition` activity log entry in `backend/app/services/contract_service.py`
- [X] T016 [US1] Implement `POST /api/v1/contracts` route handler: validate `start_date ≤ end_date`, resolve account/deal FK existence (404), return 201 `ContractResponse` in `backend/app/api/v1/contracts.py`
- [X] T017 [P] [US1] Implement `GET /api/v1/contracts/{ref_id}` route handler returning contract with nested `attachment` (null if absent) in `backend/app/api/v1/contracts.py`
- [X] T018 [P] [US1] Implement `PATCH /api/v1/contracts/{ref_id}` route handler enforcing Draft/SFR-only edit rule (400 otherwise) and ownership guard (403 for Sales Rep non-owner) in `backend/app/api/v1/contracts.py`
- [X] T019 [US1] Implement `ContractService.replace_attachment()` atomic replace: delete old disk file → delete old DB row → write new file → insert new DB row within single SQLAlchemy async transaction in `backend/app/services/contract_service.py`
- [X] T020 [US1] Implement `POST /api/v1/contracts/{ref_id}/attachment` handler: multipart upload, enforce 1 MB cap (413), MIME whitelist `pdf/docx/jpeg/png` (400), ownership guard (403), return 201 `AttachmentResponse` in `backend/app/api/v1/contracts.py`
- [X] T021 [P] [US1] Implement `DELETE /api/v1/contracts/{ref_id}/attachment` handler: disk removal + metadata row delete, 404 if absent, 403 for non-owner Sales Rep in `backend/app/api/v1/contracts.py`
- [X] T022 [P] [US1] Create `contractsApi.ts`: `createContract`, `getContract`, `updateContract`, `uploadAttachment`, `deleteAttachment` fetch wrappers in `frontend/src/services/contractsApi.ts`
- [X] T023 [P] [US1] Create TanStack Query hooks `useContract` (GET single), `useContracts` (GET list), `useMutateContract` (POST/PATCH), `useAttachmentMutation` (POST/DELETE) in `frontend/src/hooks/useContracts.ts`
- [X] T024 [P] [US1] Create `ContractStatusChip.tsx` mapping each `ContractStatus` value to a distinct MUI `Chip` colour in `frontend/src/components/contracts/ContractStatusChip.tsx`
- [X] T025 [P] [US1] Create `ContractForm.tsx` with MUI fields, inline validation (required: account, end_date, value; `start_date ≤ end_date` cross-field error), account selector in `frontend/src/components/contracts/ContractForm.tsx`
- [X] T026 [P] [US1] Create `ContractAttachmentPanel.tsx` with file picker (PDF/DOCX/image, 1 MB limit), upload progress indicator, replace and delete actions in `frontend/src/components/contracts/ContractAttachmentPanel.tsx`
- [X] T027 [US1] Create `ContractList.tsx`: paginated MUI DataGrid with `ContractStatusChip`, `ref_id` link, Renewal Due badge column (placeholder, activated in US3) in `frontend/src/components/contracts/ContractList.tsx`
- [X] T028 [US1] Create `ContractDetail.tsx`: fields section, `ContractAttachmentPanel`, activity log section placeholder in `frontend/src/components/contracts/ContractDetail.tsx`
- [X] T029 [US1] Create `ContractsPage.tsx` at route `/contracts` wrapping `ContractList` with New Contract action button in `frontend/src/pages/ContractsPage.tsx`
- [X] T030 [US1] Create `ContractDetailPage.tsx` at route `/contracts/:refId` wrapping `ContractDetail` in `frontend/src/pages/ContractDetailPage.tsx`
- [X] T031 [P] [US1] Write `backend/tests/unit/test_contract_schemas.py` covering: missing required fields (422), `start_date > end_date` (400), value precision edge cases, MIME type rejection

**Checkpoint**: User Story 1 fully functional — contract creation, file attachment, draft editing, and detail view independently testable

---

## Phase 4: User Story 2 — Manage Contract Lifecycle (Priority: P1)

**Goal**: Users advance status through Draft → SFR → Active → Expired/Terminated; Admin can revert to any prior status; system auto-expires daily; every change is logged with actor and timestamp.

**Independent Test**: Create Draft → `POST /transition` to "Sent for Review" → `POST /transition` to "Active" → `POST /transition` to "Expired"; `GET /activity` returns three log entries with correct `actor_id` and ascending timestamps.

- [X] T032 [P] [US2] Declare `VALID_TRANSITIONS` dict constant keyed by `(from_status, role) → set[ContractStatus]` in `backend/app/services/contract_service.py`
- [X] T033 [US2] Implement `ContractService.transition()` using `VALID_TRANSITIONS` table lookup, enforce mandatory `note` for backward transitions, write `status_transition` activity log entry in `backend/app/services/contract_service.py`
- [X] T034 [US2] Add activity log writes in `ContractService` for `edit`, `attachment_added`, and `attachment_removed` events in `backend/app/services/contract_service.py`
- [X] T035 [US2] Implement `POST /api/v1/contracts/{ref_id}/transition` handler: call `ContractService.transition()`, return `TransitionResponse` (400 on invalid, 403 on role/ownership violation) in `backend/app/api/v1/contracts.py`
- [X] T036 [US2] Implement `GET /api/v1/contracts/{ref_id}/activity` handler: return `ActivityLogResponse` list newest-first with `actor_name` join in `backend/app/api/v1/contracts.py`
- [X] T037 [P] [US2] Implement `expire_contracts` APScheduler job: query Active contracts where `end_date < today`, set status to Expired, write `status_transition` activity log with system actor in `backend/app/scheduler/jobs.py`
- [X] T038 [US2] Expose `POST /api/v1/internal/jobs/expire-contracts` Admin-only endpoint invoking `expire_contracts` job directly in `backend/app/api/v1/contracts.py`
- [X] T039 [US2] Register `APScheduler AsyncScheduler` at app startup with nightly `expire_contracts` cron trigger in `backend/app/main.py`
- [X] T040 [P] [US2] Add `transitionContract` and `getActivityLog` fetch wrappers to `frontend/src/services/contractsApi.ts`
- [X] T041 [P] [US2] Create `ContractTransitionDialog.tsx`: status dropdown filtered to valid forward transitions (+ all backward for Admin), note field (required indicator for backward transitions) in `frontend/src/components/contracts/ContractTransitionDialog.tsx`
- [X] T042 [P] [US2] Create `ContractActivityLog.tsx`: MUI Timeline newest-first, actor name, action type chip, note if present in `frontend/src/components/contracts/ContractActivityLog.tsx`
- [X] T043 [US2] Replace activity log placeholder and add transition button in `ContractDetail.tsx` by wiring `ContractTransitionDialog` and `ContractActivityLog` in `frontend/src/components/contracts/ContractDetail.tsx`
- [X] T044 [P] [US2] Write `backend/tests/unit/test_contract_service.py`: transition happy paths, invalid transition (400), backward without note (400), non-Admin backward attempt (403), cyclomatic complexity ≤ 5 for `transition()`
- [X] T045 [US2] Write `backend/tests/integration/test_contracts_api.py`: full CRUD, full transition chain (Draft→SFR→Active→Expired), early Termination, attachment upload/replace/delete, activity log retrieval

**Checkpoint**: User Story 2 fully functional — complete lifecycle management with audit trail independently testable

---

## Phase 5: User Story 3 — Renewal Tracking (Priority: P2)

**Goal**: Contracts expiring within 30 days are flagged `is_renewal_due=true` and owner notified in-app; owner can click Renew to create a pre-filled successor Draft with dates advanced by one term; original shows link to successor.

**Independent Test**: Create Active contract with `end_date` = today + 25 days, call `POST /internal/jobs/flag-renewals`, verify `GET /{ref_id}` returns `is_renewal_due: true`; call `POST /{ref_id}/renew`, verify 201 successor Draft with `start_date = original_end_date + 1 day` and `RenewalLink` in database.

- [X] T046 [P] [US3] Implement `flag_renewals` APScheduler job: query Active contracts where `(end_date - today) ≤ 30d` and no `RenewalLink` exists, set `is_renewal_due = true`, write `renewal_flagged` activity log in `backend/app/scheduler/jobs.py`
- [X] T047 [US3] Expose `POST /api/v1/internal/jobs/flag-renewals` Admin-only endpoint invoking `flag_renewals` job directly in `backend/app/api/v1/contracts.py`
- [X] T048 [US3] Register `flag_renewals` nightly trigger alongside `expire_contracts` in `APScheduler` startup in `backend/app/main.py`
- [X] T049 [US3] Implement `ContractService.renew()`: validate status is Active or Expired (400 otherwise), 400 if `RenewalLink` already exists, compute term length, insert successor Draft with advanced dates, insert `RenewalLink`, write `renewed` activity log on original in `backend/app/services/contract_service.py`
- [X] T050 [US3] Implement `POST /api/v1/contracts/{ref_id}/renew` handler: call `ContractService.renew()`, return 201 `RenewResponse` in `backend/app/api/v1/contracts.py`
- [X] T051 [P] [US3] Create `notificationStore.ts` — Context/Zustand store exposing `renewalDueCount` polled from `GET /api/v1/contracts?is_renewal_due=true` for in-app notification badge in `frontend/src/store/notificationStore.ts`
- [X] T052 [P] [US3] Activate Renewal Due badge in `ContractList.tsx`, add Renew action button per row, add `renewContract` wrapper to `frontend/src/services/contractsApi.ts` in `frontend/src/components/contracts/ContractList.tsx`
- [X] T053 [US3] Write `backend/tests/integration/test_scheduler_jobs.py`: expire via trigger endpoint SC-002, renewal flag via trigger endpoint SC-003, renew endpoint creates successor with correct dates (SC-005), duplicate renew blocked (400)

**Checkpoint**: User Story 3 fully functional — renewal flagging, in-app notification, and successor contract creation independently testable

---

## Phase 6: User Story 4 — Search & Filter Contracts (Priority: P2)

**Goal**: Users filter the contract list by status, account, owner, and end date range; combined filters apply simultaneously; paginated API returns results in < 1s for 10 k rows (SC-004).

**Independent Test**: Seed contracts with mixed statuses and accounts; apply `?status=Active&account_id=1`; confirm only Active contracts for account 1 returned. Apply `?end_date_from=2026-01-01&end_date_to=2026-06-30`; confirm only contracts within range returned.

- [X] T054 [P] [US4] Implement multi-predicate filter in `ContractRepository.list_paginated()` accepting `status`, `owner_id`, `account_id`, `end_date_from`, `end_date_to`, `is_archived=False` using SQLAlchemy dynamic WHERE clauses over indexed columns in `backend/app/repositories/contract_repository.py`
- [X] T055 [US4] Implement `GET /api/v1/contracts` route handler with all query parameters, `page`/`limit` pagination (max 100), 400 if `end_date_from > end_date_to`, return `ContractListResponse` in `backend/app/api/v1/contracts.py`
- [X] T056 [P] [US4] Add filter controls to `ContractList.tsx`: status select, account autocomplete, owner select, end-date-range pickers; bind to `useContracts` hook filter params in `frontend/src/components/contracts/ContractList.tsx`
- [X] T057 [P] [US4] Extend `useContracts` TanStack Query hook to accept `ContractFilterParams` and encode as URL query string in `frontend/src/hooks/useContracts.ts`
- [X] T058 [P] [US4] Write `frontend/tests/ContractList.test.tsx`: list renders contracts from mock API, filter state change triggers re-fetch, Renewal Due badge visible when `is_renewal_due=true`

**Checkpoint**: User Story 4 fully functional — all filter combinations independently testable, SC-004 achievable with indexed queries

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Remaining frontend test coverage and end-to-end validation

- [X] T059 [P] Write `frontend/tests/ContractForm.test.tsx`: required field inline validation, `start_date > end_date` cross-field error, successful submit dispatches `createContract` and redirects
- [X] T060 [P] Write `frontend/tests/ContractDetail.test.tsx`: renders all contract fields, shows `ContractAttachmentPanel`, shows `ContractActivityLog` timeline
- [X] T061 Run all quickstart.md validation scenarios SC-001 through SC-006 against local dev stack (`curl` scripts from quickstart.md) and confirm each success criterion passes

**Checkpoint**: All user stories delivered, validated against success criteria, and ready for peer review per constitution governance

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Phase 2 — no dependency on other user stories
- **US2 (Phase 4)**: Depends on Phase 2 — wires into ContractDetail from US1 at T043
- **US3 (Phase 5)**: Depends on Phase 2 — extends ContractList from US1 at T052
- **US4 (Phase 6)**: Depends on Phase 2 — extends ContractRepository (T054) and ContractList (T056) from Phase 2/US1
- **Polish (Phase 7)**: Depends on US1–US4 completions

### User Story Dependencies

- **US1 (P1)**: Independently startable after Phase 2
- **US2 (P1)**: Independently startable after Phase 2; T043 integrates into US1 ContractDetail
- **US3 (P2)**: Independently startable after Phase 2; T052 integrates into US1 ContractList
- **US4 (P2)**: Independently startable after Phase 2; T055 adds to contracts.py router, T054 adds to repository, T056/T057 extend ContractList/hooks

### Within Each User Story

- Backend: models (Phase 2) → services → route handlers
- Frontend: types (Phase 2) → API wrappers → Query hooks → Components → Pages
- Integration points requiring coordination: T043 (US2 into Detail), T052 (US3 into List), T056 (US4 into List)

### Parallel Opportunities

- T002, T003, T004 parallel with T001 (Phase 1)
- T008, T009, T010, T011 parallel after T007 (Phase 2)
- US1 and US2 can be worked by separate developers in parallel once Phase 2 complete
- US3 and US4 can be worked by separate developers in parallel once Phase 2 complete
- All [P]-marked tasks within a phase are safe to parallelize

---

## Parallel Example: User Story 1

```bash
# After T015 (ContractService.create) completes, these backend handlers are independent:
T017: GET /contracts/{ref_id} — different handler function
T018: PATCH /contracts/{ref_id} — different handler function
T021: DELETE /contracts/{ref_id}/attachment — different handler function

# Frontend tasks are all independent of each other (different files):
T022: contractsApi.ts wrappers
T023: TanStack Query hooks
T024: ContractStatusChip.tsx
T025: ContractForm.tsx
T026: ContractAttachmentPanel.tsx
T031: test_contract_schemas.py
```

---

## Parallel Example: User Story 2

```bash
# After Phase 2 complete, these US2 tasks are independent of each other:
T032: VALID_TRANSITIONS constant (same file as T033, but just a declaration)
T037: expire_contracts scheduler job — backend/app/scheduler/jobs.py
T040: transitionContract API wrapper — frontend/src/services/contractsApi.ts
T041: ContractTransitionDialog.tsx — new component file
T042: ContractActivityLog.tsx — new component file
T044: test_contract_service.py — new test file
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (**CRITICAL — blocks all stories**)
3. Complete Phase 3: User Story 1 (T014–T031)
4. **STOP and VALIDATE**: Run SC-001 `curl` scenario from quickstart.md
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → project skeleton with DB schema
2. US1 → Sales Rep can create, view, edit, and attach files (MVP demo)
3. US2 → Full lifecycle with audit trail + auto-expiry scheduler
4. US3 → Renewal flagging and successor contract creation
5. US4 → Search and filter at 10 k scale (SC-004)
6. Polish → Frontend test coverage, lint, SC-001–SC-006 final validation

### Parallel Team Strategy (3 developers)

After Phase 2 complete:
- **Dev A**: US1 (T014–T031) — backend create/edit/attach + frontend form/detail/list
- **Dev B**: US2 (T032–T045) — lifecycle transitions + scheduler + dialog/timeline
- **Dev C**: US3 + US4 (T046–T058) — renewal jobs + filter layer

Coordinate on merge conflicts at T043 (Dev B into ContractDetail from Dev A), T052 (Dev C into ContractList from Dev A), and T056/T057 (Dev C extending hooks/list from Dev A).

---

## Notes

- `[P]` tasks touch different files and have no unresolved upstream dependency — safe to parallelize
- `[US#]` label maps each task to a specific user story for independent progress tracking
- Backend tests use `pytest-asyncio` + `httpx.AsyncClient` against in-memory SQLite (research.md Decision 3) — no mocking of DB layer
- Attachment storage at runtime: `backend/attachments/{contract_id}/{filename}` — add to `.gitignore`
- Scheduler trigger endpoints (`/internal/jobs/*`) serve as test hooks per plan.md Decision 3 — same job function runs in both cron and manual invocation
- Constitution IV (Security First): ownership guards and role checks implemented at T010/T018/T020/T033/T035 — cover in security review before merge
- Constitution NFR (p95 ≤ 200ms): T054 filter query MUST use only indexed columns (`status`, `owner_id`, `account_id`, `end_date`) — verify query plan before merging
- Cyclomatic complexity ≤ 10 per function (constitution): `ContractService.transition()` uses table lookup to stay ≤ 5 (plan.md Decision 1)
