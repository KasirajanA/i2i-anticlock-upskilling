# Tasks: Sales Pipeline

**Feature Branch**: `002-sales-pipeline`
**Input**: Design documents from `specs/002-sales-pipeline/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/api.md ✅, quickstart.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[US#]**: Maps to user story from spec.md
- Each task includes exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project skeleton per plan.md structure

- [X] T001 Create backend directory structure: `backend/app/{core,models,schemas,repositories,services,scheduler,api/v1}`, `backend/tests/{unit,integration}`, `backend/alembic/versions`, `backend/app/scripts/`
- [X] T002 [P] Create frontend directory structure: `frontend/src/{types,services,hooks,components/pipeline,pages,store}`, `frontend/tests/{components,hooks}/`
- [X] T003 [P] Create `backend/requirements.txt` with FastAPI, Pydantic v2, SQLAlchemy 2.x, aiosqlite, APScheduler 4.x, Uvicorn, Alembic, pytest, pytest-asyncio, httpx, ruff
- [X] T004 [P] Initialize `frontend/package.json` and `frontend/vite.config.ts` with React 18, MUI v6, TanStack Query v5, Vite, Vitest, React Testing Library, msw (Mock Service Worker)

**Checkpoint**: Project skeleton ready — dependency installation can begin

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, schemas, repository base, and security layer — MUST be complete before any user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create Alembic migration `backend/alembic/versions/002_create_pipeline_tables.py` for `deals`, `deal_comments`, `activity_log` tables including all FK constraints, the `is_overdue`/`is_archived` boolean columns, and all eight indexes from data-model.md
- [X] T006 Define `DealStage` StrEnum (all six values, `is_terminal` property, `probability()` classmethod) and `Deal` ORM model (all columns, relationships to comments/activity/owner/account/contact) in `backend/app/models/deal.py`
- [X] T007 Add `DealComment` (soft-delete via `is_deleted`) and `ActivityLog` ORM models (action_type, actor_id, note) to `backend/app/models/deal.py`
- [X] T008 [P] Create all Pydantic v2 schemas: `DealCreate`, `DealUpdate`, `DealRead`, `DealSummary`, `DealListResponse` in `backend/app/schemas/deal.py`; `CommentCreate`, `CommentRead`, `CommentListResponse` in `backend/app/schemas/deal_comment.py`; `ActivityLogRead`, `ActivityLogResponse` in `backend/app/schemas/activity_log.py`; `ForecastResponse`, `StageTotal` in `backend/app/schemas/forecast.py`; `StageChangeRequest`, `StageChangeResponse` in `backend/app/schemas/deal.py`
- [X] T009 [P] Implement `ActivityRepository` with `insert_log(deal_id, action_type, actor_id, note)` and `fetch_for_deal(deal_id)` async methods in `backend/app/repositories/activity_repository.py`
- [X] T010 [P] Extend `backend/app/core/security.py` with `require_team_scope(deal, current_user)` helper that enforces Sales Rep team-visibility rule (FR-006)
- [X] T011 [P] Create TypeScript types `Deal`, `DealStage`, `DealComment`, `ActivityLog`, `ForecastResponse`, `StageTotal`, `DealListResponse` in `frontend/src/types/deal.ts`
- [X] T012 Create `DealService` skeleton class with async session and `ActivityRepository` dependency injection in `backend/app/services/deal_service.py`
- [X] T013 Create `backend/app/api/v1/deals.py` and `backend/app/api/v1/pipeline.py` APIRouter skeletons; register both under `/api/v1` in `backend/app/main.py`

**Checkpoint**: Foundation ready — all four user stories can now be implemented in parallel

---

## Phase 3: User Story 1 — Create & Manage a Deal (Priority: P1) 🎯 MVP

**Goal**: Sales Rep can create a deal with DEAL-NNNN ref_id, update its fields, add comments, and view the full activity log; deal appears in the paginated deal list.

**Independent Test**: `POST /api/v1/deals` with title, value, stage, close date, owner, account returns 201 with `ref_id: "DEAL-0001"`; `GET /api/v1/deals` returns it in items; `PATCH /api/v1/deals/DEAL-0001` updates value; `GET /api/v1/deals/DEAL-0001/activity` shows `deal_created` and `field_updated` entries.

- [X] T014 [US1] Implement DEAL-NNNN ref_id auto-generation (padded sequential counter) in `backend/app/services/deal_service.py`
- [X] T015 [US1] Implement `DealService.create()`: persist deal row, write `deal_created` activity log entry, dispatch in-app notification if owner differs from actor (FR-011 assignment notification) in `backend/app/services/deal_service.py`
- [X] T016 [US1] Implement `DealService.update()`: update editable fields, write `field_updated` activity log entry per changed field in `backend/app/services/deal_service.py`
- [X] T017 [P] [US1] Implement `DealRepository.list_paginated()` with multi-predicate WHERE (stage, owner_id, account_id, is_overdue, is_archived=False) + team-scope subquery for Sales Rep role in `backend/app/repositories/deal_repository.py`
- [X] T018 [US1] Implement `POST /api/v1/deals` route handler: validate account_id exists (400), enforce team-scope on owner_id (403), return 201 `DealRead` in `backend/app/api/v1/deals.py`
- [X] T019 [P] [US1] Implement `GET /api/v1/deals` list handler: delegate to `DealRepository.list_paginated()`, return `DealListResponse` (page, limit, total, items) in `backend/app/api/v1/deals.py`
- [X] T020 [P] [US1] Implement `GET /api/v1/deals/{ref_id}` handler: 404 if not found or outside team scope in `backend/app/api/v1/deals.py`
- [X] T021 [P] [US1] Implement `PATCH /api/v1/deals/{ref_id}` handler: 403 for Sales Rep non-owner, call `DealService.update()`, return updated `DealRead` in `backend/app/api/v1/deals.py`
- [X] T022 [US1] Implement `GET /api/v1/deals/{ref_id}/comments` (paginated) and `POST /api/v1/deals/{ref_id}/comments` handlers (empty body → 400) in `backend/app/api/v1/deals.py`
- [X] T023 [US1] Implement `GET /api/v1/deals/{ref_id}/activity` handler returning `ActivityLogResponse` ordered by `created_at` ASC in `backend/app/api/v1/deals.py`
- [X] T024 [P] [US1] Create `dealService.ts`: `createDeal`, `listDeals`, `getDeal`, `updateDeal`, `getComments`, `addComment`, `getActivity` fetch wrappers in `frontend/src/services/dealService.ts`
- [X] T025 [P] [US1] Create `useDeals.ts`: `useDeals` (list with filters), `useDeal` (single), `useCreateDeal`, `usePatchDeal` TanStack Query hooks in `frontend/src/hooks/useDeals.ts`
- [X] T026 [P] [US1] Create `useComments.ts`: `useComments` (list) and `useAddComment` (mutation) TanStack Query hooks in `frontend/src/hooks/useComments.ts`
- [X] T027 [P] [US1] Create `DealForm.tsx`: MUI modal form with inline validation (required: title, value ≥ 0, close date, account; stage selector with all 6 DealStage values) in `frontend/src/components/pipeline/DealForm.tsx`
- [X] T028 [US1] Create `DealDetailPanel.tsx`: side panel showing deal fields, comments list with add-comment input, activity log timeline in `frontend/src/components/pipeline/DealDetailPanel.tsx`
- [X] T029 [P] [US1] Write `backend/tests/integration/test_comments_api.py`: add comment (201), list comments (200), empty body (400), auth rules (view-gated)
- [X] T030 [P] [US1] Write `backend/tests/integration/test_activity_api.py`: `deal_created` entry on create, `field_updated` entry on patch, ordering ascending
- [X] T031 [P] [US1] Write `frontend/tests/components/DealForm.test.tsx`: required field inline validation blocks submit, valid form dispatches `createDeal`
- [X] T032 [P] [US1] Write `frontend/tests/hooks/useDeals.test.ts`: query hook returns paginated list from msw mock, filter params encoded correctly in URL

**Checkpoint**: User Story 1 fully functional — create, list, update, comment, and view activity independently testable

---

## Phase 4: User Story 2 — Move Deals Through Pipeline Stages (Priority: P1)

**Goal**: Users drag deals between stages; each move is logged; Closed Won/Lost are terminal; Closed Lost requires a loss reason; is_overdue is cleared on close.

**Independent Test**: Create deal in "Qualified" → `POST /api/v1/deals/DEAL-0001/stage` with `{"stage":"Proposal"}` → confirm 200 with `previous_stage:"Qualified"`, `new_stage:"Proposal"`; `GET /activity` shows `stage_changed` entry. Attempt second stage change on Closed Won → confirm 422 with code `TERMINAL_STAGE`.

- [X] T033 [US2] Implement `DealService.change_stage()`: terminal stage guard (422 `TERMINAL_STAGE`), loss_reason enforcement for Closed Lost (422 `LOSS_REASON_REQUIRED`), clear `is_overdue` on Closed transition, write `stage_changed` activity log with `"Lead In → Qualified"` note format in `backend/app/services/deal_service.py`
- [X] T034 [US2] Implement `POST /api/v1/deals/{ref_id}/stage` route handler: call `DealService.change_stage()`, return `StageChangeResponse` (ref_id, previous_stage, new_stage, is_overdue, updated_at) in `backend/app/api/v1/deals.py`
- [X] T035 [P] [US2] Create `useStageChange.ts`: TanStack Query mutation with optimistic update (board card moves instantly) and rollback on API error in `frontend/src/hooks/useStageChange.ts`
- [X] T036 [P] [US2] Create `StageChangeModal.tsx`: stage select dropdown (non-terminal options), conditional `loss_reason` textarea (required and visible only when Closed Lost selected) in `frontend/src/components/pipeline/StageChangeModal.tsx`
- [X] T037 [P] [US2] Write `backend/tests/unit/test_deal_service.py`: stage change happy path, terminal guard (422), loss_reason missing (422), is_overdue cleared on close, `stage_changed` log note format, ref_id generation sequence
- [X] T038 [US2] Write `backend/tests/integration/test_deals_api.py`: create deal (201), list (200), patch (200), stage change chain (Lead In → Proposal → Closed Won), terminal guard (422), loss_reason required (422), Sales Rep non-owner patch (403)
- [X] T039 [P] [US2] Write `frontend/tests/hooks/useStageChange.test.ts`: optimistic update applies immediately, rollback restores previous stage on API 422 error

**Checkpoint**: User Story 2 fully functional — complete stage lifecycle with terminal guard and activity log independently testable

---

## Phase 5: User Story 3 — Pipeline Board View (Priority: P1)

**Goal**: Sales Rep sees all their open deals as cards in a Kanban board grouped by stage; Manager/Admin see all deals; overdue deals show a visual flag; board is filterable by owner, account, and close date range.

**Independent Test**: Create 3 deals across 3 stages, open `GET /api/v1/deals` — confirm each appears with correct stage; run overdue job trigger for deal with past close date — confirm `is_overdue=true`; open `/pipeline` route — confirm board renders three stage columns each with the correct deal card.

- [X] T040 [P] [US3] Implement `flag_overdue_deals` APScheduler job: query open deals where `expected_close_date < today` and stage is non-terminal, set `is_overdue=true`, insert `overdue_flagged` activity log + in-app notification per owner (FR-011) in `backend/app/scheduler/jobs.py`
- [X] T041 [US3] Register `APScheduler AsyncScheduler` at app startup with nightly `flag_overdue_deals` cron (01:00 UTC); expose `POST /api/v1/internal/jobs/flag-overdue` Admin-only trigger endpoint in `backend/app/main.py` and `backend/app/api/v1/deals.py`
- [X] T042 [P] [US3] Create `pipelineFilters.ts` Zustand slice: state for `stage`, `owner_id`, `account_id`, `is_overdue`, `close_date_from`, `close_date_to` filter params with setters in `frontend/src/store/pipelineFilters.ts`
- [X] T043 [P] [US3] Create `DealCard.tsx`: MUI Card displaying deal title, account name, value (formatted currency), close date, `is_overdue` warning badge, click handler to open `DealDetailPanel` in `frontend/src/components/pipeline/DealCard.tsx`
- [X] T044 [P] [US3] Create `StageColumn.tsx`: MUI column container showing stage label, deal count, `DealCard` list, drag-and-drop drop target accepting deal cards in `frontend/src/components/pipeline/StageColumn.tsx`
- [X] T045 [US3] Create `PipelineBoard.tsx`: six `StageColumn` instances (Lead In through Closed Lost), drag-and-drop orchestration calling `useStageChange`, `StageChangeModal` trigger on drop in `frontend/src/components/pipeline/PipelineBoard.tsx`
- [X] T046 [US3] Create `PipelinePage.tsx` at route `/pipeline`: renders `PipelineBoard` + filter bar (owner select, account autocomplete, is_overdue toggle, date range pickers) bound to `pipelineFilters` store in `frontend/src/pages/PipelinePage.tsx`
- [X] T047 [P] [US3] Write `backend/tests/integration/test_overdue_job.py`: overdue flag set on past-close deal, notification row created in notifications table, flag cleared when deal transitions to Closed Won, already-closed deals not re-flagged
- [X] T048 [P] [US3] Write `frontend/tests/components/PipelineBoard.test.tsx`: board renders six stage columns from msw-mocked deal list, drag triggers `useStageChange` mutation
- [X] T049 [P] [US3] Write `frontend/tests/components/DealCard.test.tsx`: card shows title/value/close date, overdue badge visible when `is_overdue=true`, no badge when `is_overdue=false`

**Checkpoint**: User Story 3 fully functional — Kanban board with overdue flagging and team-scoped visibility independently testable

---

## Phase 6: User Story 4 — Deal Forecasting Summary (Priority: P2)

**Goal**: Manager/Admin views open pipeline totals grouped by stage with weighted probability values and a Closed Won summary for a configurable date range (SC-004: accurate to the cent).

**Independent Test**: Seed one deal per non-closed stage with known values (Lead In 10 000, Qualified 20 000, Proposal 30 000, Negotiation 40 000, all closing in Q3 2026); call `GET /api/v1/pipeline/forecast?period=2026-07-01/2026-09-30`; verify `total_weighted_forecast = 51000.00` and each stage `weighted_value` matches probability × total_value.

- [X] T050 [P] [US4] Implement `DealRepository.forecast_aggregate(period_start, period_end)`: single `SELECT stage, COUNT(*), SUM(value) … GROUP BY stage` query scoped to non-archived, non-Closed-Lost deals within the date range, returning raw stage totals in `backend/app/repositories/deal_repository.py`
- [X] T051 [US4] Implement `DealService.get_forecast(period_start, period_end)`: call `DealRepository.forecast_aggregate()`, apply `DealStage.probability()` to each stage total, assemble `ForecastResponse` (open_pipeline list, closed_won total, total_weighted_forecast) using `Decimal` arithmetic (zero rounding error) in `backend/app/services/deal_service.py`
- [X] T052 [US4] Implement `GET /api/v1/pipeline/forecast` handler: parse `period` ISO range param (default: current calendar quarter), 400 on invalid format, 403 for Sales Rep/Support Agent role, return `ForecastResponse` in `backend/app/api/v1/pipeline.py`
- [X] T053 [P] [US4] Create `useForecast.ts`: `useForecast(period?: string)` TanStack Query hook wrapping `GET /api/v1/pipeline/forecast` in `frontend/src/hooks/useForecast.ts`
- [X] T054 [P] [US4] Create `ForecastTable.tsx`: MUI table with open pipeline rows (stage, deal_count, total_value, probability %, weighted_value) and a Closed Won summary row; format all values with 2 decimal places in `frontend/src/components/pipeline/ForecastTable.tsx`
- [X] T055 [US4] Create `ForecastPage.tsx` at route `/pipeline/forecast`: hosts `ForecastTable` + period range picker (current quarter default; next quarter option) in `frontend/src/pages/ForecastPage.tsx`
- [X] T056 [P] [US4] Write `backend/tests/unit/test_forecast_service.py`: probability mapping for all six stages, `Decimal` arithmetic produces zero rounding error on SC-003 test values, closed stages excluded from open pipeline, 403 enforcement
- [X] T057 [US4] Write `backend/tests/integration/test_forecast_api.py`: seed deals with known values across stages and close dates, verify exact `total_value`, `weighted_value`, and `total_weighted_forecast` match SC-003 expected table; confirm Closed Lost deals excluded; confirm period filter restricts results
- [X] T058 [P] [US4] Write `frontend/tests/components/ForecastTable.test.tsx`: renders stage rows from msw-mocked forecast response, weighted values formatted to 2 d.p., Closed Won row shown separately

**Checkpoint**: User Story 4 fully functional — SC-004 accuracy verifiable against seed data, Manager-only access enforced

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and cross-module integration check

- [X] T059 Run quickstart.md validation scenarios SC-001 through SC-003 against local dev stack: seed 500 deals (SC-001 board load < 2s), stage change flow (SC-002 log visible immediately), forecast with known values (SC-003 accurate to the cent)

**Checkpoint**: All user stories validated, pipeline board and forecast meeting success criteria, ready for peer review

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **US1 (Phase 3)**: Independently startable after Phase 2 — no dependency on other stories
- **US2 (Phase 4)**: Independently startable after Phase 2 — T034 adds to deals.py started in US1; T038 extends test_deals_api.py
- **US3 (Phase 5)**: Independently startable after Phase 2 — T045 PipelineBoard depends on T035 (useStageChange from US2)
- **US4 (Phase 6)**: Independently startable after Phase 2 — uses DealRepository from Phase 2; DealService.get_forecast() adds to deal_service.py
- **Polish (Phase 7)**: Depends on all four stories complete

### User Story Dependencies

- **US1 (P1)**: Independent after Phase 2 — creates deals list endpoint and DealRepository used by all stories
- **US2 (P1)**: Independent after Phase 2 — adds stage change endpoint to deals.py; PipelineBoard (US3) depends on useStageChange (US2 T035)
- **US3 (P1)**: Depends on US2's `useStageChange` hook (T035) for drag-and-drop; otherwise independent
- **US4 (P2)**: Independent after Phase 2 — separate repository method, separate API router

### Within Each User Story

- Backend: DealStage enum + ORM (Phase 2) → service methods → route handlers
- Frontend: TypeScript types (Phase 2) → API wrappers → Query hooks → Components → Pages
- Integration points: US2 extends deals.py (T034 after T022); US3 PipelineBoard imports useStageChange (T035 before T045)

### Parallel Opportunities

- T002, T003, T004 run in parallel with T001 (Phase 1)
- T008, T009, T010, T011 run in parallel after T007 (Phase 2)
- Within US1: T017–T020 backend handlers [P] after T016; T024–T027 frontend [P] simultaneously
- Within US2: T035, T036, T037 run in parallel with T033/T034
- Within US3: T040, T042, T043, T044 run in parallel; T045 waits for T043+T044
- Within US4: T050, T053, T054 run in parallel; T051 waits for T050
- US1 + US2 can be worked by separate developers simultaneously once Phase 2 complete
- US3 + US4 can be worked by separate developers simultaneously once US2 T035 is complete

---

## Parallel Example: User Story 1

```bash
# After T016 (DealService.update) completes, these handlers are independent:
T017: DealRepository.list_paginated() — different file
T019: GET /deals list handler — different function
T020: GET /deals/{ref_id} handler — different function
T021: PATCH /deals/{ref_id} handler — different function

# These frontend tasks are all independent (different files):
T024: dealService.ts wrappers
T025: useDeals.ts hooks
T026: useComments.ts hooks
T027: DealForm.tsx
T029: test_comments_api.py
T030: test_activity_api.py
T031: DealForm.test.tsx
T032: useDeals.test.ts
```

---

## Parallel Example: User Story 3

```bash
# After Phase 2 complete, these US3 tasks are all independent:
T040: flag_overdue_deals scheduler job (backend/app/scheduler/jobs.py)
T042: pipelineFilters.ts Zustand store
T043: DealCard.tsx component
T044: StageColumn.tsx component

# T045 PipelineBoard must wait for T043 + T044:
T045: PipelineBoard.tsx (depends on DealCard + StageColumn)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (**CRITICAL — blocks all stories**)
3. Complete Phase 3: User Story 1 (T014–T032)
4. **STOP and VALIDATE**: `curl` deal create + list from quickstart.md
5. Deploy/demo deal creation on board

### Incremental Delivery

1. Setup + Foundational → DB schema, models, base service
2. US1 → Sales Rep can create, view, edit deals, add comments (MVP demo)
3. US2 → Full stage pipeline with terminal guard and audit trail
4. US3 → Kanban board with drag-and-drop + overdue flagging + notifications
5. US4 → Forecast view with weighted pipeline totals (SC-003 accuracy)
6. Polish → SC-001 through SC-003 final validation

### Parallel Team Strategy (3 developers)

After Phase 2 complete:
- **Dev A**: US1 (T014–T032) — CRUD backend + DealForm/DealDetailPanel frontend
- **Dev B**: US2 (T033–T039) — stage transitions + StageChangeModal + useStageChange
- **Dev C**: US4 (T050–T058) — forecast aggregate + ForecastTable frontend

Dev C can start US4 in parallel with Dev A/B since it only touches `deal_repository.py` (new method), `deal_service.py` (new method), and `api/v1/pipeline.py` (new file).

After US2 complete (T035 done), Dev A or new dev starts US3 (T040–T049) which requires `useStageChange` hook.

Coordinate on merge conflicts at `deal_service.py` (US1 T015/T016 vs US2 T033 vs US4 T051) and `deal_repository.py` (US1 T017 vs US4 T050).

---

## Notes

- `[P]` tasks touch different files and have no unresolved upstream dependency — safe to parallelize
- `[US#]` label maps each task to a specific user story for per-story progress tracking
- Backend tests use `pytest-asyncio` + `httpx.AsyncClient` against in-memory SQLite (research.md Decision 3) — no DB mocking
- Frontend tests use `msw` for API mocking (research.md Decision 3) — tests exercise hooks and components against realistic responses
- Overdue job trigger endpoint (`/internal/jobs/flag-overdue`) doubles as a test hook — same job function used in both nightly cron and manual invocation (research.md Decision 2)
- Free-flow stage transitions (Decision 1): only the `is_terminal` guard in `DealService.change_stage()` — no transition matrix required
- Forecast Decimal arithmetic: use Python `Decimal` throughout `get_forecast()` to avoid floating-point rounding (SC-004 requires cent-accurate totals)
- Constitution NFR (p95 ≤ 200ms): T017 `DealRepository.list_paginated()` MUST use indexed columns only — `idx_deals_owner_stage`, `idx_deals_is_overdue`, `idx_deals_account_id`
- Cyclomatic complexity ≤ 10: `DealService.change_stage()` uses `DealStage.is_terminal` property + two guard clauses = complexity 4 (plan.md constitution check)
- FR-006 team-scoping implemented in T010 (security helper) and T017 (repository subquery) — covered in security review before merge
