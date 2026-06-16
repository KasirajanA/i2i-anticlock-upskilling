# Tasks: Analytics & Reporting

**Feature Branch**: `004-analytics-reporting`
**Input**: Design documents from `specs/004-analytics-reporting/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/api.md ✅, quickstart.md ✅

**Key constraint**: Read-only module — zero new DB tables; all aggregations run against tables owned by modules 001–003, 006–007.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[US#]**: Maps to user story from spec.md
- Each task includes exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project skeleton per plan.md structure

- [X] T001 Create backend directory structure: `backend/app/{schemas,repositories,services,api/v1}` analytics sub-paths, `backend/tests/{unit,integration}` (analytics files)
- [X] T002 [P] Create frontend directory structure: `frontend/src/{types,services,hooks,components/analytics,pages}`, `frontend/tests/`
- [X] T003 [P] Add `cachetools` to `backend/requirements.txt` (only new backend dependency for this module)
- [X] T004 [P] Add `date-fns` to `frontend/package.json` for date range formatting (only new frontend dependency)

**Checkpoint**: Project skeleton ready — no new migrations needed (read-only module)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared schemas, query builder, cache manager, CSV streamer, and reusable frontend components — MUST be complete before any user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create all Pydantic v2 analytics schemas in `backend/app/schemas/analytics.py`: `WidgetItem`, `DashboardResponse`, `StageBreakdownItem`, `RepRevenue`, `SalesReportResponse`, `StatusBreakdownItem`, `PriorityBreakdownItem`, `PerAgentCount`, `SupportReportResponse`, `StatusValueItem`, `UpcomingRenewal`, `AccountValue`, `ContractReportResponse`, `ReportFiltersApplied`
- [X] T006 [P] Create `ReportQueryBuilder` class with `with_role_scope(user)` (forces `owner_id` for Sales Rep/Support Agent), `with_date_range(after, before)`, `_apply_archive_policy()` (no `deleted_at` filter on aggregates per FR-011), and empty `build_*_report()` method stubs in `backend/app/services/report_query_builder.py`
- [X] T007 [P] Create `ReportCacheKey` dataclass and `CacheManager` with two `TTLCache` instances (`support`: 60s, `default`: 300s), `asyncio.Lock`, `get_or_set(key, factory)`, and `CacheInvalidator.invalidate(report_type)` version counter in `backend/app/services/cache_manager.py`
- [X] T008 [P] Create `AnalyticsRepository` skeleton with `AsyncSession` injection and empty async method stubs for each report type in `backend/app/repositories/analytics_repository.py`
- [X] T009 [P] Create `CSVStreamer` with `stream_rows(query_result, columns)` generator yielding 500-row chunks as `StreamingResponse` with correct `Content-Disposition` header in `backend/app/services/csv_streamer.py`
- [X] T010 [P] Create TypeScript types in `frontend/src/types/analytics.ts`: `DashboardWidget`, `DashboardResponse`, `SalesReportResponse`, `SupportReportResponse`, `ContractReportResponse`, `ReportFilters`, `UpcomingRenewal`, `PerAgentCount`, `StageBreakdown`
- [X] T011 [P] Create `analyticsApi.ts`: `getDashboard`, `getSalesReport`, `getSupportReport`, `getContractReport`, `exportSalesReport`, `exportSupportReport`, `exportContractReport` fetch wrappers (export wrappers trigger browser download via `Blob`) in `frontend/src/services/analyticsApi.ts`
- [X] T012 [P] Create `useAnalytics.ts` base file: export `REPORT_STALE_TIME = 4 * 60 * 1000`, `SUPPORT_STALE_TIME = 50 * 1000`, `GC_TIME = 10 * 60 * 1000` constants; stub `useDashboard`, `useSalesReport`, `useSupportReport`, `useContractReport` hook signatures in `frontend/src/hooks/useAnalytics.ts`
- [X] T013 [P] Create `ReportFilterBar.tsx`: date range pickers (default: current calendar month), owner/agent select (hidden for Sales Rep / Support Agent roles, visible for Manager/Admin) in `frontend/src/components/analytics/ReportFilterBar.tsx`
- [X] T014 [P] Create `ReportTable.tsx`: reusable MUI `DataGrid` accepting typed `columns` and `rows` props; renders `(deactivated)` indicator on rows where user is inactive (FR-010) in `frontend/src/components/analytics/ReportTable.tsx`
- [X] T015 [P] Create `CacheTimer.tsx` ("Refreshing in X min" countdown reading `cached_until` prop) and `ExportButton.tsx` (download trigger with loading/disabled state during fetch) in `frontend/src/components/analytics/CacheTimer.tsx` and `frontend/src/components/analytics/ExportButton.tsx`
- [X] T016 Create router skeletons `analytics_dashboard.py`, `analytics_sales.py`, `analytics_support.py`, `analytics_contracts.py` under `backend/app/api/v1/`; register all under `/api/v1/analytics` prefix in `backend/app/main.py`

**Checkpoint**: Foundation ready — all four user stories can now be implemented in parallel

---

## Phase 3: User Story 1 — Personal Dashboard (Priority: P1) 🎯 MVP

**Goal**: Logged-in user lands on a role-specific dashboard; Sales Rep sees own deal metrics; Support Agent sees own ticket metrics; Manager/Admin see org-wide summaries; widgets loaded in parallel for ≤ 2 s (SC-001).

**Independent Test**: Log in as Sales Rep with 3 seeded open deals; `GET /api/v1/analytics/dashboard` returns `open_deals_count: 3` and correct `pipeline_value`; no ticket or org-wide widgets in response. Repeat as Support Agent and Admin — confirm role-specific widget sets.

- [X] T017 [US1] Implement `WIDGET_REGISTRY` per-role mapping (`Role → list[widget_fn]`) for all 11 widget keys from data-model.md in `backend/app/services/dashboard_service.py`
- [X] T018 [US1] Implement `DashboardService.get_widgets(user)` using `asyncio.gather()` to run all role-specific widget queries in parallel; return `DashboardResponse` in `backend/app/services/dashboard_service.py`
- [X] T019 [US1] Implement `AnalyticsRepository` aggregate query methods for all 11 widget keys (each a single `COUNT(*)`/`SUM()` SQL aggregate with role-scoped `WHERE`) in `backend/app/repositories/analytics_repository.py`
- [X] T020 [US1] Implement `GET /api/v1/analytics/dashboard` handler: call `DashboardService.get_widgets(current_user)`, no cache (live per FR-008), return `DashboardResponse` in `backend/app/api/v1/analytics_dashboard.py`
- [X] T021 [P] [US1] Create `DashboardWidget.tsx`: MUI `Card` tile showing icon (MUI icon by widget key), numeric value, label, unit in `frontend/src/components/analytics/DashboardWidget.tsx`
- [X] T022 [P] [US1] Create `DashboardGrid.tsx`: responsive MUI `Grid` rendering a list of `DashboardWidget` tiles; renders MUI `Skeleton` during loading in `frontend/src/components/analytics/DashboardGrid.tsx`
- [X] T023 [P] [US1] Implement `useDashboard` hook in `useAnalytics.ts`: `useQuery` with `queryKey: ['dashboard']`, `staleTime: 0` (always live on page load) in `frontend/src/hooks/useAnalytics.ts`
- [X] T024 [US1] Create `DashboardPage.tsx` at route `/dashboard`: renders `DashboardGrid` fed by `useDashboard`; displays `generated_at` timestamp in `frontend/src/pages/DashboardPage.tsx`
- [X] T025 [P] [US1] Write `backend/tests/integration/test_dashboard_api.py`: Sales Rep sees own-data widgets only, Support Agent sees own-ticket widgets only, Admin sees org-wide widgets, widget values match seeded data counts, response is not cached (two sequential calls return fresh data)
- [X] T026 [P] [US1] Write `frontend/tests/Dashboard.test.tsx`: renders correct widget tiles from mocked API response per role, shows Skeleton during loading

**Checkpoint**: User Story 1 fully functional — role-specific dashboard with parallel widget queries independently testable

---

## Phase 4: User Story 2 — Sales Pipeline Report (Priority: P1)

**Goal**: Manager/Admin sees deal totals by stage, won/lost ratio, avg deal value, and top reps for a date range; Sales Rep sees only own data; CSV export streams scoped rows; 5-min cache; role-scope violation returns 403.

**Independent Test**: Seed 5 deals with known values/stages/owners across two reps; `GET /api/v1/analytics/reports/sales?created_after=2026-06-01&created_before=2026-06-30` as Manager returns correct stage totals; same request as Sales Rep returns only own deals; `GET .../sales?owner_id=<other_id>` as Sales Rep returns 403.

- [X] T027 [US2] Implement `ReportQueryBuilder.build_sales_report()`: stage breakdown (`GROUP BY stage`), won/lost counts, average deal value, top 10 reps by closed revenue (`SUM(value) … GROUP BY owner_id ORDER BY DESC LIMIT 10`), all with role scope and date range applied; archive inclusion enforced via `_apply_archive_policy()` in `backend/app/services/report_query_builder.py`
- [X] T028 [US2] Implement `AnalyticsRepository.execute_sales_report(filters, user)`: instantiate `ReportQueryBuilder`, build queries, execute via `AsyncSession`, assemble `SalesReportResponse`, pass through `CacheManager.get_or_set()` with 300s TTL in `backend/app/repositories/analytics_repository.py`
- [X] T029 [US2] Implement `GET /api/v1/analytics/reports/sales` handler: enforce Sales Rep `owner_id` override (403 if different ID requested), parse date range (422 if `after > before` or range > 366d), delegate to `AnalyticsRepository`, return `SalesReportResponse` with `cached_until` in `backend/app/api/v1/analytics_sales.py`
- [X] T030 [P] [US2] Implement `GET /api/v1/analytics/reports/sales/export` handler: same role-scope check, call `CSVStreamer` with deal-level rows (deal_id, title, owner, stage, value, outcome, close_date), return `StreamingResponse` with `text/csv` and filename header in `backend/app/api/v1/analytics_sales.py`
- [X] T031 [P] [US2] Implement `useSalesReport(filters: ReportFilters)` hook in `useAnalytics.ts`: `useQuery` with `queryKey: ['report', 'sales', filters]`, `staleTime: REPORT_STALE_TIME` (4 min) in `frontend/src/hooks/useAnalytics.ts`
- [X] T032 [US2] Create `SalesReportPage.tsx` at route `/reports/sales`: `ReportFilterBar` (date range + owner select for Manager/Admin, hidden for Sales Rep), `ReportTable` for stage breakdown, won/lost summary row, average deal value metric, top-reps table, `CacheTimer`, `ExportButton` in `frontend/src/pages/SalesReportPage.tsx`
- [X] T033 [P] [US2] Write `backend/tests/integration/test_sales_report_api.py`: stage breakdown totals match seed data (SC-006), date filter restricts results, Sales Rep sees only own deals, `owner_id` override by Sales Rep returns 403 (SC-005), export returns valid CSV with correct scope
- [X] T034 [P] [US2] Write `frontend/tests/SalesReport.test.tsx`: filter controls render (owner select hidden for Sales Rep role), `ReportTable` shows stage rows from mocked response, `ExportButton` triggers download fetch

**Checkpoint**: User Story 2 fully functional — sales report with date filter, role scope, and CSV export independently testable

---

## Phase 5: User Story 3 — Support Performance Report (Priority: P1)

**Goal**: Manager/Admin sees ticket volume by status/priority, avg resolution time, SLA breach rate, and per-agent counts; Support Agent sees only own tickets; 1-minute cache TTL for SLA freshness (FR-008).

**Independent Test**: Seed tickets with known statuses, priorities, resolution times, and one SLA breach; `GET /api/v1/analytics/reports/support` as Manager returns correct `status_breakdown`, `avg_resolution_hours`, and `sla_breach_rate` matching seed; `cached_until` is ≤ 1 minute ahead; Support Agent sees only own-ticket metrics.

- [X] T035 [US3] Implement `ReportQueryBuilder.build_support_report()`: status breakdown (`GROUP BY status`), priority breakdown (`GROUP BY priority`), avg resolution time (`AVG(resolved_at - created_at)` for resolved tickets), SLA breach rate (`COUNT(breached) / COUNT(total)` on active `sla_records`), per-agent counts (`GROUP BY assignee_id`), all with role scope and date range in `backend/app/services/report_query_builder.py`
- [X] T036 [US3] Implement `AnalyticsRepository.execute_support_report(filters, user)`: build and execute support queries, assemble `SupportReportResponse`, pass through `CacheManager.get_or_set()` with **60s TTL** (support cache instance) in `backend/app/repositories/analytics_repository.py`
- [X] T037 [US3] Implement `GET /api/v1/analytics/reports/support` handler: enforce Support Agent `assignee_id` override (403 if different ID), delegate to `AnalyticsRepository`, return `SupportReportResponse` with `cached_until` ≤ 1 min ahead in `backend/app/api/v1/analytics_support.py`
- [X] T038 [P] [US3] Implement `GET /api/v1/analytics/reports/support/export` handler: ticket-level rows (ticket_id, subject, status, priority, assignee, created_at, resolved_at) scoped to caller, stream via `CSVStreamer` in `backend/app/api/v1/analytics_support.py`
- [X] T039 [P] [US3] Implement `useSupportReport(filters: ReportFilters)` hook in `useAnalytics.ts`: `useQuery` with `staleTime: SUPPORT_STALE_TIME` (50s — refreshes before 60s server cache expires) in `frontend/src/hooks/useAnalytics.ts`
- [X] T040 [US3] Create `SupportReportPage.tsx` at route `/reports/support`: `ReportFilterBar` (date range + agent select for Manager/Admin), status breakdown `ReportTable`, priority breakdown `ReportTable`, avg resolution time metric, SLA breach rate metric, per-agent `ReportTable`, `CacheTimer` (1-min label), `ExportButton` in `frontend/src/pages/SupportReportPage.tsx`
- [X] T041 [P] [US3] Write `backend/tests/integration/test_support_report_api.py`: status/priority counts match seed, SLA breach rate calculation correct, `cached_until` ≤ 60 s ahead (not 300 s), Support Agent sees only own tickets, per-agent list includes deactivated agent with `(deactivated)` label (FR-010)
- [X] T042 [P] [US3] Write `frontend/tests/SupportReport.test.tsx`: status breakdown table renders from mocked response, `CacheTimer` shows "Refreshing in 1 minute", SLA breach rate displayed correctly

**Checkpoint**: User Story 3 fully functional — support report with 1-minute SLA cache, per-agent breakdown, and CSV export independently testable

---

## Phase 6: User Story 4 — Contract Expiry Report (Priority: P2)

**Goal**: Admin/Manager sees contracts grouped by status with total values, upcoming renewals filtered by 30/60/90-day window, and value by account; Sales Rep sees only own contracts; 5-min cache; renewal window validates as one of 30/60/90.

**Independent Test**: Seed contracts expiring at 15 days, 45 days, and 100 days from today; `GET /api/v1/analytics/reports/contracts?renewal_window=60` returns only the 15-day and 45-day contracts in `upcoming_renewals`; `renewal_window=99` returns 422.

- [X] T043 [US4] Implement `ReportQueryBuilder.build_contract_report()`: status breakdown (`GROUP BY status, SUM(value)`), upcoming renewals (`WHERE expiry_date BETWEEN NOW() AND NOW() + {window}d`, ordered by expiry ASC), value by account (`SUM(value) GROUP BY account_id`), all with role scope applied in `backend/app/services/report_query_builder.py`
- [X] T044 [US4] Implement `AnalyticsRepository.execute_contract_report(filters, user)`: build and execute contract queries, assemble `ContractReportResponse` with `days_remaining` computed per renewal row, pass through `CacheManager.get_or_set()` with 300s TTL in `backend/app/repositories/analytics_repository.py`
- [X] T045 [US4] Implement `GET /api/v1/analytics/reports/contracts` handler: validate `renewal_window` is one of `{30, 60, 90}` (422 otherwise), enforce Sales Rep `owner_id` scope (403 if override attempted), delegate to `AnalyticsRepository`, return `ContractReportResponse` in `backend/app/api/v1/analytics_contracts.py`
- [X] T046 [P] [US4] Implement `GET /api/v1/analytics/reports/contracts/export` handler: contract-level rows (contract_id, account_name, owner, status, value, start_date, expiry_date, days_remaining) scoped to caller, stream via `CSVStreamer` in `backend/app/api/v1/analytics_contracts.py`
- [X] T047 [P] [US4] Implement `useContractReport(filters: ContractFilters)` hook in `useAnalytics.ts`: `useQuery` with `queryKey: ['report', 'contracts', filters]`, `staleTime: REPORT_STALE_TIME` (4 min) in `frontend/src/hooks/useAnalytics.ts`
- [X] T048 [US4] Create `ContractReportPage.tsx` at route `/reports/contracts`: renewal window selector (MUI `Select` with 30/60/90 options, default 30), status breakdown `ReportTable` (status, count, total_value), upcoming renewals `ReportTable` (account, value, expiry_date, days_remaining sorted ASC), value-by-account `ReportTable`, `CacheTimer`, `ExportButton` in `frontend/src/pages/ContractReportPage.tsx`
- [X] T049 [P] [US4] Write `backend/tests/integration/test_contract_report_api.py`: renewal window 30/60/90 filters correctly, `renewal_window=99` returns 422, status breakdown values match seed (SC-006), Sales Rep sees only own contracts (SC-005), export scoped correctly
- [X] T050 [P] [US4] Write `frontend/tests/ContractReport.test.tsx`: renewal window selector changes filter params, upcoming renewals table renders days_remaining, ExportButton triggers download

**Checkpoint**: User Story 4 fully functional — contract report with renewal window filter, role scope, and CSV export independently testable

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Unit test coverage for shared infrastructure components validated across all stories

- [X] T051 [P] Write `backend/tests/unit/test_report_query_builder.py`: role scope forces `owner_id` for Sales Rep/Support Agent, Manager/Admin has no owner filter, date range injection, `_apply_archive_policy()` omits `deleted_at IS NULL`, `filters_hash` changes with different params
- [X] T052 [P] Write `backend/tests/unit/test_cache_manager.py`: TTL expiry returns fresh result after 60s/300s, version invalidation clears cache entry immediately, concurrent reads via asyncio lock return consistent value, support cache uses 60s not 300s TTL
- [X] T053 [P] Write `backend/tests/unit/test_csv_streamer.py`: 500-row chunking, column ordering preserved, `Content-Disposition` filename matches report type, role-scoped rows count matches expected
- [X] T054 Run quickstart.md Scenarios 1–7 against local dev stack: role-specific dashboard (SC-001), sales date filter (SC-003), support SLA freshness (FR-008 1-min cache), contract renewal window, CSV export (SC-004), role scope 403 (SC-005), deactivated user label (FR-010)

**Checkpoint**: All user stories validated, role-scoping verified (SC-005), aggregation accuracy confirmed (SC-006)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user stories**; no migrations (read-only module)
- **US1 (Phase 3)**: Independently startable after Phase 2 — uses `AnalyticsRepository` from T008
- **US2 (Phase 4)**: Independently startable after Phase 2 — uses `ReportQueryBuilder` (T006), `CacheManager` (T007), `CSVStreamer` (T009)
- **US3 (Phase 5)**: Independently startable after Phase 2 — extends `ReportQueryBuilder` (T035) and `AnalyticsRepository` (T036) with support-specific methods
- **US4 (Phase 6)**: Independently startable after Phase 2 — extends `ReportQueryBuilder` (T043) and `AnalyticsRepository` (T044) with contract-specific methods
- **Polish (Phase 7)**: Depends on all four stories complete

### User Story Dependencies

- **US1 (P1)**: Independent after Phase 2 — adds `DashboardService` (new file), widget queries to `AnalyticsRepository`
- **US2 (P1)**: Independent after Phase 2 — adds sales methods to `ReportQueryBuilder` and `AnalyticsRepository`; `analytics_sales.py` is a separate file
- **US3 (P1)**: Independent after Phase 2 — adds support methods to same `ReportQueryBuilder`/`AnalyticsRepository`; `analytics_support.py` separate file
- **US4 (P2)**: Independent after Phase 2 — adds contract methods to same shared classes; `analytics_contracts.py` separate file

### Coordination Points

US2, US3, US4 all extend `report_query_builder.py` and `analytics_repository.py` — coordinate merges on these two files. Each story adds new **methods** (no modifications to existing methods), so merge conflicts should be straightforward.

### Within Each User Story

- Backend: `ReportQueryBuilder` method → `AnalyticsRepository` method → route handler
- Frontend: hook → page component (using shared `ReportFilterBar`, `ReportTable`, `CacheTimer`, `ExportButton` from Phase 2)

### Parallel Opportunities

- T002, T003, T004 parallel with T001 (Phase 1)
- T006–T015 all parallel after T005 (Phase 2 — all independent files)
- Within US1: T021, T022, T023, T025, T026 all parallel
- Within US2: T030, T031, T033, T034 parallel with T027/T028/T029
- Within US3: T038, T039, T041, T042 parallel
- Within US4: T046, T047, T049, T050 parallel
- US1 + US2 + US3 + US4 can all be worked concurrently after Phase 2 (different files, coordinate on 2 shared service files)
- T051, T052, T053 all parallel in Polish

---

## Parallel Example: User Story 1

```bash
# After T019 (AnalyticsRepository widget queries) completes:
T020: GET /dashboard handler        — analytics_dashboard.py

# All frontend tasks are independent (different files):
T021: DashboardWidget.tsx
T022: DashboardGrid.tsx
T023: useDashboard hook
T025: test_dashboard_api.py
T026: Dashboard.test.tsx
```

---

## Parallel Example: Full Module (4 developers)

```bash
# After Phase 2 complete (T005-T016):
Dev A: US1 (T017-T026)  — DashboardService + DashboardPage
Dev B: US2 (T027-T034)  — SalesReport + analytics_sales.py
Dev C: US3 (T035-T042)  — SupportReport + analytics_support.py
Dev D: US4 (T043-T050)  — ContractReport + analytics_contracts.py

# Each dev extends report_query_builder.py and analytics_repository.py
# with NEW methods — merge in order B → C → D (or rebase cleanly)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (schemas, query builder, cache, CSV streamer, shared components — **CRITICAL**)
3. Complete Phase 3: User Story 1 (T017–T026)
4. **STOP and VALIDATE**: Run quickstart.md Scenario 1 (role-specific dashboard loads in ≤ 2 s)
5. Deploy/demo: every user has a working dashboard after login

### Incremental Delivery

1. Setup + Foundational → shared infrastructure ready (no user-facing feature yet)
2. US1 → Personal Dashboard (MVP — first screen after login)
3. US2 → Sales Pipeline Report with date filter + CSV export
4. US3 → Support Performance Report with 1-min SLA cache
5. US4 → Contract Expiry Report with renewal window
6. Polish → Unit tests for shared infrastructure + SC-001–SC-006 validation

### Parallel Team Strategy

All four user stories can be worked in parallel after Phase 2 completes. The only coordination required is on two shared backend files (`report_query_builder.py` and `analytics_repository.py`) — each story only adds new methods to these files, so parallel development with rebase-on-merge is safe.

---

## Notes

- `[P]` tasks touch different files and have no unresolved upstream dependency — safe to parallelize
- `[US#]` label maps each task to a specific user story for per-story progress tracking
- **No DB migrations** — this module reads from tables owned by modules 001–003, 006–007
- **Role scope is non-negotiable** (SC-005): enforced in `ReportQueryBuilder.with_role_scope()` at query construction time, not in post-processing — prevents bypass via pagination offset attacks (research.md section 2)
- **Archive inclusion** (FR-011): `_apply_archive_policy()` explicitly omits `deleted_at IS NULL` from all report aggregates — enforced at query builder layer, not caller-controlled (research.md section 7)
- **Cache TTL split**: support report uses 60s cache instance; all others use 300s instance — `CacheManager` selects by `ReportCacheKey.report_type` (research.md section 1)
- **Deactivated users** (FR-010): `ReportTable.tsx` renders `(deactivated)` indicator; `AnalyticsRepository` joins `users.is_active` flag on per-agent rows
- **CSV export** uses same scoped query as the report view — same `ReportQueryBuilder` instance, no separate scope check needed (research.md section 3)
- **asyncio.gather()** in `DashboardService.get_widgets()` ensures all widget queries run concurrently — critical for SC-001 (≤ 2 s dashboard load, research.md section 4)
- Constitution IV (Security First): `owner_id` override for Sales Rep returns 403 at route handler level (T029/T037/T045) — verified by SC-005 integration tests
