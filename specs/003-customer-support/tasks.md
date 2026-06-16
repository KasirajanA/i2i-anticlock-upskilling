# Tasks: Customer Support

**Feature Branch**: `003-customer-support`
**Input**: Design documents from `specs/003-customer-support/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/api.md ✅, quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[US#]**: Maps to user story from spec.md
- Each task includes exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project skeleton per plan.md structure

- [X] T001 Create backend directory structure: `backend/app/{core,models,schemas,repositories,services,scheduler,api/v1}`, `backend/tests/{unit,integration}`
- [X] T002 [P] Create frontend directory structure: `frontend/src/{types,services,hooks,components/support,pages}`, `frontend/tests/`
- [X] T003 [P] Create `backend/requirements.txt` with FastAPI, Uvicorn, SQLAlchemy 2.x, aiosqlite, APScheduler 4.x, Pydantic v2, Alembic, pytest, pytest-asyncio, httpx, ruff
- [X] T004 [P] Initialize `frontend/package.json` and `frontend/vite.config.ts` with React 18, MUI v6, TanStack Query v5, Vite, Vitest, React Testing Library, TypeScript 5

**Checkpoint**: Project skeleton ready — dependency installation can begin

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core ORM models, schemas, repository abstraction, activity logger, and service skeleton — MUST be complete before any user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create Alembic migration `backend/alembic/versions/003_create_support_tables.py` for `tickets`, `ticket_sequence`, `replies`, `sla_records`, `ticket_activity_log` tables including all FK constraints, NOT NULL defaults, and all indexes from data-model.md (`(status, created_at)`, `(assignee_id, status)`, `(ticket_id, is_active)`, etc.)
- [X] T006 Define `TicketStatus` and `TicketPriority` enums plus `Ticket` ORM model (all columns including `contact_name_snapshot`, `deleted_at` soft-delete) in `backend/app/models/support.py`
- [X] T007 Add `Reply`, `SLARecord` (with `cycle`, `is_active`, breach booleans), `TicketActivityLog` (JSON `metadata`), and `TicketSequence` ORM models to `backend/app/models/support.py`
- [X] T008 [P] Create all Pydantic v2 request/response schemas: `TicketCreate`, `TicketRead`, `TicketListResponse`, `TicketUpdate`, `SLARecordRead`, `ReplyCreate`, `ReplyRead`, `ReplyListResponse`, `ActivityLogRead`, `ActivityLogResponse`, `AssignRequest` in `backend/app/schemas/support.py`
- [X] T009 [P] Create `ITicketRepository` abstract base class with method stubs (`create`, `get_by_id`, `list_paginated`, `update`, `assign`) in `backend/app/repositories/base.py`
- [X] T010 Create `SqliteTicketRepository(ITicketRepository)` skeleton class with async session injection and empty method stubs in `backend/app/repositories/sqlite_ticket_repository.py`
- [X] T011 [P] Create `ActivityLogger` service with `append(session, ticket_id, event_type, actor_id, metadata)` async method in `backend/app/services/activity_logger.py`
- [X] T012 [P] Create TypeScript types `Ticket`, `TicketStatus`, `TicketPriority`, `Reply`, `SLARecord`, `ActivityLogEntry`, `TicketListResponse` in `frontend/src/types/support.ts`
- [X] T013 Create `TicketService` skeleton with `ITicketRepository` + `ActivityLogger` + `SLAEngine` dependency injection in `backend/app/services/ticket_service.py`
- [X] T014 Create router skeletons `support_tickets.py`, `support_replies.py`, `support_activity.py`, `_test.py` under `backend/app/api/v1/`; register all under `/api/v1/support` prefix in `backend/app/main.py`

**Checkpoint**: Foundation ready — all four user stories can now be implemented in parallel

---

## Phase 3: User Story 1 — Create a Support Ticket (Priority: P1) 🎯 MVP

**Goal**: Support Agent creates a ticket with auto-generated `I2I-CRM-NNNN` ref, linked contact (with name snapshot), priority, and SLA record; ticket appears in the queue with status `open`.

**Independent Test**: `POST /api/v1/support/tickets` with subject, priority `high`, contact_id → 201 with `ref: "I2I-CRM-0001"`, `status: "open"`, `sla.first_response_due` ~4h from now; `GET /api/v1/support/tickets` returns it under `queue=mine` and `queue=unassigned`.

- [X] T015 [US1] Implement `TicketIDGenerator`: `UPDATE ticket_sequence SET next_value = next_value + 1 RETURNING next_value` inside the create transaction; format as `I2I-CRM-{n:04d}` in schema in `backend/app/services/ticket_service.py`
- [X] T016 [US1] Implement `TicketService.create_ticket()`: ID generation, capture `contact_name_snapshot` from contacts table, create `SLARecord` (cycle 1, compute due dates via `SLAEngine`), write `creation` activity log entry in `backend/app/services/ticket_service.py`
- [X] T017 [US1] Implement `SqliteTicketRepository.create()` and `get_by_id()` (with active SLA record join) in `backend/app/repositories/sqlite_ticket_repository.py`
- [X] T018 [US1] Implement `POST /api/v1/support/tickets` handler: 422 if `contact_id` missing/invalid, 403 if caller lacks support/admin role, return 201 `TicketRead` in `backend/app/api/v1/support_tickets.py`
- [X] T019 [P] [US1] Implement `GET /api/v1/support/tickets/{ticket_id}` handler returning ticket with active `SLARecord` nested, 404 if not found in `backend/app/api/v1/support_tickets.py`
- [X] T020 [P] [US1] Implement `GET /api/v1/support/tickets` list handler with cursor pagination (`(status, created_at, id)` cursor), `queue` param (mine/unassigned/all), and all filter params from contracts/api.md in `backend/app/api/v1/support_tickets.py`
- [X] T021 [P] [US1] Create `supportApi.ts`: `createTicket`, `getTicket`, `listTickets` (with cursor support) fetch wrappers in `frontend/src/services/supportApi.ts`
- [X] T022 [P] [US1] Create `useTickets.ts`: `useInfiniteQuery` hook with cursor-based pagination, `getNextPageParam` from `next_cursor` in `frontend/src/hooks/useTickets.ts`
- [X] T023 [P] [US1] Create `TicketStatusChip.tsx`: MUI `Chip` with distinct colour per `TicketStatus` value in `frontend/src/components/support/TicketStatusChip.tsx`
- [X] T024 [P] [US1] Create `PriorityBadge.tsx`: MUI `Chip` with distinct colour per `TicketPriority` value (Critical = error, High = warning, Medium = info, Low = default) in `frontend/src/components/support/PriorityBadge.tsx`
- [X] T025 [US1] Create `TicketRow.tsx`: shared list row with `TicketStatusChip`, `PriorityBadge`, contact name, assignee name, SLA indicator placeholder in `frontend/src/components/support/TicketRow.tsx`
- [X] T026 [US1] Create `TicketQueue.tsx`: filterable, cursor-paginated list using `useTickets` and `TicketRow`; accepts `queue` prop (`mine` | `unassigned` | `all`) in `frontend/src/components/support/TicketQueue.tsx`
- [X] T027 [US1] Create `NewTicketPage.tsx` at route `/support/new`: form with subject (required), priority select, contact selector, description; inline validation blocks empty submit in `frontend/src/pages/NewTicketPage.tsx`
- [X] T028 [P] [US1] Write `backend/tests/unit/test_ticket_id_generator.py`: sequential counter increments correctly, formats as `I2I-CRM-0001` through `I2I-CRM-9999`, transaction-safe under concurrent inserts

**Checkpoint**: User Story 1 fully functional — ticket creation, queue listing, and SLA record bootstrap independently testable

---

## Phase 4: User Story 2 — Manage Ticket Lifecycle (Priority: P1)

**Goal**: Agent advances ticket Open → In Progress → Resolved → Closed; replies set `first_response_at`; customer reply on Resolved ticket auto-reopens with new SLA cycle; all changes logged.

**Independent Test**: `PATCH` ticket to `in_progress` → `POST /replies` (non-internal) → `PATCH` to `resolved` → verify `sla.first_response_at` set and `resolved_at` set; `POST /replies` on resolved ticket → verify status back to `open`, `cycle: 2` SLA record created, original SLA `is_active: false`.

- [X] T029 [US2] Implement `ALLOWED_TRANSITIONS` + `ADMIN_REVERSIONS` dicts and `TicketService.transition()` method (422 on invalid, 403 for agent revert) with `status_change` activity log entry in `backend/app/services/ticket_service.py`
- [X] T030 [US2] Implement `TicketService.add_reply()`: set `first_response_at` on first non-internal reply (if unset), trigger re-open if ticket is `resolved` (deactivate old SLARecord, create new cycle), dispatch assignment notification, write `reply_added` or `note_added` activity log in `backend/app/services/ticket_service.py`
- [X] T031 [US2] Implement `PATCH /api/v1/support/tickets/{ticket_id}` handler: delegate status to `TicketService.transition()`, handle field updates, return updated `TicketRead` in `backend/app/api/v1/support_tickets.py`
- [X] T032 [P] [US2] Implement `GET /api/v1/support/tickets/{ticket_id}/replies` and `POST /api/v1/support/tickets/{ticket_id}/replies` handlers; filter internal notes for non-agent callers in `backend/app/api/v1/support_replies.py`
- [X] T033 [US2] Implement `GET /api/v1/support/tickets/{ticket_id}/activity` handler returning `TicketActivityLog` entries newest-first in `backend/app/api/v1/support_activity.py`
- [X] T034 [P] [US2] Create `useTicketMutations.ts`: `useUpdateTicket` (PATCH status/fields), `useAddReply` (POST reply) TanStack Query mutations with cache invalidation in `frontend/src/hooks/useTicketMutations.ts`
- [X] T035 [P] [US2] Create `ReplyForm.tsx`: `body` textarea (required, max 10 000 chars), `is_internal` toggle checkbox, submit dispatches `useAddReply` in `frontend/src/components/support/ReplyForm.tsx`
- [X] T036 [P] [US2] Create `ActivityTimeline.tsx`: MUI `Timeline` rendering `TicketActivityLog` entries with `event_type` icon, actor name, metadata summary, newest-first in `frontend/src/components/support/ActivityTimeline.tsx`
- [X] T037 [US2] Create `TicketDetail.tsx`: ticket header (subject, status, priority, assignee), status-transition action buttons (role-filtered), `ReplyForm`, reply thread, `ActivityTimeline`; assignee section placeholder (filled in US3) in `frontend/src/components/support/TicketDetail.tsx`
- [X] T038 [US2] Create `TicketDetailPage.tsx` at route `/support/tickets/:ticketId` wrapping `TicketDetail` in `frontend/src/pages/TicketDetailPage.tsx`
- [X] T039 [P] [US2] Write `backend/tests/unit/test_ticket_service.py`: valid transitions, invalid transition (422), agent revert blocked (403), re-open creates cycle 2 SLARecord, original SLARecord set inactive, `first_response_at` only set once
- [X] T040 [P] [US2] Write `backend/tests/integration/test_replies_api.py`: add reply (201), re-open trigger on resolved ticket, internal note hidden from non-agent, `first_response_at` set on first non-internal reply
- [X] T041 [P] [US2] Write `frontend/tests/ReplyForm.test.tsx`: empty body blocked, `is_internal` toggle renders, submit calls `useAddReply`
- [X] T042 [P] [US2] Write `frontend/tests/TicketDetail.test.tsx`: transition buttons visible per role, reply thread renders, SLA section present (SLAIndicator wired in US4)

**Checkpoint**: User Story 2 fully functional — complete lifecycle, reply thread, auto-reopen, and audit trail independently testable

---

## Phase 5: User Story 3 — Ticket Assignment & Queue Management (Priority: P1)

**Goal**: Admin assigns tickets to agents; agents self-assign unassigned tickets; My Tickets / Unassigned / All Tickets queues show correct scoping; orphaned tickets (inactive assignee) surfaced with Admin alert.

**Independent Test**: Create two tickets — assign one to agent, leave one unassigned; `GET /tickets?queue=mine` as agent returns only assigned ticket; `GET /tickets?queue=unassigned` returns the unassigned one; `POST /{ticket_id}/assign` self-assigns it and moves it to agent's queue.

- [X] T043 [US3] Implement `TicketService.assign()`: validate `assignee_id` references active user with support/admin role, dispatch in-app notification to new assignee, write `assignment` activity log in `backend/app/services/ticket_service.py`
- [X] T044 [US3] Implement `POST /api/v1/support/tickets/{ticket_id}/assign` handler: agents may only assign to themselves (403 otherwise), Admins assign to any active user in `backend/app/api/v1/support_tickets.py`
- [X] T045 [US3] Implement `SqliteTicketRepository.list_paginated()` with full multi-predicate WHERE (status, priority, assignee_id, account_id, created_after/before, queue scope) + cursor in `backend/app/repositories/sqlite_ticket_repository.py`
- [X] T046 [P] [US3] Create `SupportQueuePage.tsx` at route `/support`: MUI Tabs for My Tickets / Unassigned / All Tickets each rendering `TicketQueue` with correct `queue` prop in `frontend/src/pages/SupportQueuePage.tsx`
- [X] T047 [P] [US3] Add assignee display, Assign to Me button (for unassigned tickets), and reassign select (Admin only) to `TicketDetail.tsx` in `frontend/src/components/support/TicketDetail.tsx`
- [X] T048 [P] [US3] Write `backend/tests/integration/test_tickets_api.py`: create (201), get (200), list with queue=mine/unassigned/all scoping, assign endpoint (self-assign + admin assign + 403 cross-assign), cursor pagination, role enforcement (403/401)
- [X] T049 [P] [US3] Write `frontend/tests/TicketQueue.test.tsx`: My/Unassigned/All tabs render correct queue prop, filter controls update query params, empty state shown when no tickets, infinite scroll loads next page

**Checkpoint**: User Story 3 fully functional — three-queue view with assignment and team-scoping independently testable

---

## Phase 6: User Story 4 — SLA Tracking (Priority: P2)

**Goal**: Each ticket has SLA due dates per priority; APScheduler polls every 5 minutes to flag breaches; `SLAIndicator` shows countdown/warning/breach badge; Admin receives in-app notification on breach; test endpoints enable clock-advance without waiting.

**Independent Test**: Create Critical ticket (1h first-response SLA); call `POST /api/v1/_test/sla/advance-clock?minutes=65` + `POST /api/v1/_test/jobs/run-sla-check`; verify `GET /tickets/{id}/sla` returns `first_response_breached: true`; verify Admin notification created; `SLAIndicator` in queue shows breach badge.

- [X] T050 [P] [US4] Implement `SLAEngine` class with `SLA_POLICY` dict injected via constructor, `compute_due_dates(priority, from_dt)` returning `(first_response_due, resolution_due)`, and `check_breaches(session)` async method that flags records and returns breached ticket IDs in `backend/app/services/sla_engine.py`
- [X] T051 [US4] Implement APScheduler 5-minute `sla_breach_job`: call `SLAEngine.check_breaches()`, dispatch in-app notification to all Admin users for each newly breached ticket in `backend/app/scheduler/jobs.py`
- [X] T052 [US4] Register `APScheduler AsyncScheduler` at startup with `sla_breach_job` on a 5-minute interval in `backend/app/main.py`
- [X] T053 [P] [US4] Implement `GET /api/v1/support/tickets/{ticket_id}/sla` handler returning all `SLARecord` rows for a ticket (all cycles) in `backend/app/api/v1/support_tickets.py`
- [X] T054 [US4] Implement test-only endpoints in `backend/app/api/v1/_test.py` (enabled only when `ENVIRONMENT=test`): `POST /api/v1/_test/sla/advance-clock?minutes=N` (adjusts a `_clock_offset` used by `SLAEngine`) and `POST /api/v1/_test/jobs/run-sla-check` (triggers `sla_breach_job` synchronously)
- [X] T055 [P] [US4] Create `SLAIndicator.tsx`: countdown timer to `first_response_due` or `resolution_due`, MUI colour chip showing `OK` / `Warning` (< 1h remaining) / `Breached` with `aria-label` in `frontend/src/components/support/SLAIndicator.tsx`
- [X] T056 [US4] Wire `SLAIndicator` into `TicketRow.tsx` (compact mode using `first_response_due`, `first_response_breached`) and `TicketDetail.tsx` (full SLA panel with both due dates) in `frontend/src/components/support/TicketRow.tsx` and `frontend/src/components/support/TicketDetail.tsx`
- [X] T057 [P] [US4] Write `backend/tests/unit/test_sla_engine.py`: `compute_due_dates` per all four priorities, `check_breaches` sets `first_response_breached=true` when past due, warning threshold (< 1h), no re-flag on already-breached records
- [X] T058 [P] [US4] Write `frontend/tests/SLAIndicator.test.tsx`: renders OK when time remains, renders Warning badge when < 1h, renders Breached badge when `first_response_breached=true`, has correct `aria-label`

**Checkpoint**: User Story 4 fully functional — SLA breach detection, notification, and visual indicator independently testable via clock-advance test endpoints

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation against all quickstart scenarios

- [X] T059 Run quickstart.md Scenarios 1–7 against local dev stack: ticket creation (SC-001), lifecycle flow (Scenario 2), SLA breach via clock-advance (SC-002/Scenario 3), customer reply re-open (SC-004/Scenario 4), queue management (Scenario 5), inline validation (Scenario 6), filter controls (Scenario 7)

**Checkpoint**: All user stories validated against success criteria, SLA scheduler verified, ready for peer review

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **US1 (Phase 3)**: Independently startable after Phase 2
- **US2 (Phase 4)**: Independently startable after Phase 2 — extends `TicketService` (T013) and route handlers from US1 (T031 adds to support_tickets.py, T032 uses support_replies.py)
- **US3 (Phase 5)**: Independently startable after Phase 2 — T045 completes `SqliteTicketRepository.list_paginated()` used by US1 T020; T047 extends `TicketDetail.tsx` from US2 T037
- **US4 (Phase 6)**: Independently startable after Phase 2 — `SLAEngine` is a standalone service; T056 extends `TicketRow.tsx` (US1 T025) and `TicketDetail.tsx` (US2 T037)
- **Polish (Phase 7)**: Depends on all four stories complete

### User Story Dependencies

- **US1 (P1)**: Independent after Phase 2
- **US2 (P1)**: Independent after Phase 2; T031 adds PATCH handler to `support_tickets.py` (T018 from US1); T037 `TicketDetail` extends US1's `TicketRow` components
- **US3 (P1)**: Independent after Phase 2; T047 extends `TicketDetail.tsx` from US2 T037
- **US4 (P2)**: Independent after Phase 2; T056 extends `TicketRow.tsx` (US1 T025) and `TicketDetail.tsx` (US2 T037)

### Within Each User Story

- Backend: ORM models (Phase 2) → repository methods → service methods → route handlers
- Frontend: TypeScript types (Phase 2) → API wrappers → Query hooks → Primitive components → Composite components → Pages
- Integration points requiring coordination: US2 (T031 extends support_tickets.py); US3 (T047 extends TicketDetail); US4 (T056 extends TicketRow + TicketDetail)

### Parallel Opportunities

- T002, T003, T004 parallel with T001 (Phase 1)
- T008, T009, T011, T012 parallel after T007 (Phase 2)
- Within US1: T019, T020 parallel after T018; T021–T024 all parallel (different files)
- Within US2: T032, T034–T036, T039–T042 all parallel with sequential T029/T030/T031
- Within US3: T046, T047, T048, T049 parallel after T043–T045
- Within US4: T050, T053, T055, T057, T058 parallel; T051 depends on T050

---

## Parallel Example: User Story 1

```bash
# After T018 (POST create handler) completes, backend handlers are independent:
T019: GET /tickets/{ticket_id}      — different handler function
T020: GET /tickets list             — different handler function

# All frontend tasks are independent (different files):
T021: supportApi.ts wrappers
T022: useTickets.ts infinite query hook
T023: TicketStatusChip.tsx
T024: PriorityBadge.tsx
T028: test_ticket_id_generator.py
```

---

## Parallel Example: User Story 2

```bash
# After T030 (TicketService.add_reply) completes:
T032: GET+POST /replies handlers    — support_replies.py (different file from support_tickets.py)

# Frontend and test tasks are all independent:
T034: useTicketMutations.ts
T035: ReplyForm.tsx
T036: ActivityTimeline.tsx
T039: test_ticket_service.py
T040: test_replies_api.py
T041: ReplyForm.test.tsx
T042: TicketDetail.test.tsx
```

---

## Parallel Example: User Story 4

```bash
# All independent after Phase 2:
T050: SLAEngine class         — backend/app/services/sla_engine.py
T053: GET /sla handler        — new endpoint, no conflict with other US4 work
T055: SLAIndicator.tsx        — new frontend component
T057: test_sla_engine.py      — unit tests for standalone SLAEngine
T058: SLAIndicator.test.tsx   — frontend component tests
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (**CRITICAL — blocks all stories**)
3. Complete Phase 3: User Story 1 (T015–T028)
4. **STOP and VALIDATE**: Run quickstart.md Scenario 1 and Scenario 6
5. Deploy/demo: agents can create tickets and see them in the queue

### Incremental Delivery

1. Setup + Foundational → DB schema, ORM, skeleton services
2. US1 → Agent creates ticket, appears in queue (MVP demo, SC-001)
3. US2 → Full lifecycle + replies + auto-reopen + audit trail (SC-004)
4. US3 → Three-queue view, assignment, orphan handling (SC-005)
5. US4 → SLA tracking, breach detection, visual indicators (SC-002)
6. Polish → Scenarios 1–7 validated end-to-end

### Parallel Team Strategy (3 developers)

After Phase 2 complete:
- **Dev A**: US1 (T015–T028) — ticket creation, queue list, ID generator, frontend form/queue
- **Dev B**: US2 (T029–T042) — lifecycle transitions, replies, re-open, activity timeline
- **Dev C**: US4 (T050–T058) — SLAEngine standalone, SLAIndicator component (no US3 dependency)

After US1 + US2 complete: Dev A or new dev picks up US3 (T043–T049).

Coordinate on merge conflicts at:
- `ticket_service.py` (US1 T016/T015 vs US2 T029/T030 vs US3 T043)
- `support_tickets.py` (US1 T018/T019/T020 vs US2 T031 vs US3 T044 vs US4 T053)
- `TicketDetail.tsx` (US2 T037 vs US3 T047 vs US4 T056)
- `TicketRow.tsx` (US1 T025 vs US4 T056)

---

## Notes

- `[P]` tasks touch different files and have no unresolved upstream dependency — safe to parallelize
- `[US#]` label maps each task to a specific user story for per-story progress tracking
- Backend tests use `pytest-asyncio` + `httpx.AsyncClient` against in-memory SQLite (research.md section 6)
- Re-open logic lives entirely in `TicketService.add_reply()` — single entry point (research.md section 4)
- `TicketIDGenerator` uses `UPDATE ticket_sequence … RETURNING` inside the create transaction — guaranteed unique under SQLite WAL serialisation (research.md section 1)
- Test-only endpoints (`_test.py`) MUST check `ENVIRONMENT=test` before executing — never enabled in production
- `SLAEngine` receives `SLA_POLICY` via constructor injection (constitution II — Dependency Inversion); adding a new priority level requires zero changes to `SLAEngine` (constitution II — Open/Closed)
- `TicketRow.tsx` is reused verbatim in My Tickets, Unassigned, and All Tickets queues (constitution III — DRY)
- Constitution IV (Security First): agent status-revert blocked at service layer (T029), role check at route layer (T018/T031/T044)
- Constitution NFR (p95 ≤ 200ms): T045 list query MUST use composite indexes `(status, created_at)` and `(assignee_id, status)` — verify query plan before merging
- `contact_name_snapshot` is captured at creation (T016) and preserved permanently — contact deletion MUST NOT be blocked by FK constraint (FR-011); verify FK is NULLABLE in T005 migration
