# Implementation Plan: Analytics & Reporting

**Branch**: `004-analytics-reporting` | **Date**: 2026-06-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-analytics-reporting/spec.md`

---

## Summary

Build a read-only analytics layer over the CRM's source data: a role-specific personal dashboard, Sales/Support/Contract reports with date filters and CSV export, strict role-scoped data access (Sales Rep / Support Agent see only own data; Manager / Admin see org-wide data), and an in-process TTL cache (5 min general, 1 min SLA data). Backend: Python 3.14 + FastAPI (async) + SQLAlchemy 2.x/aiosqlite. Frontend: React 18 + TypeScript + MUI v6.

---

## Technical Context

**Language/Version**: Python 3.14 (backend), TypeScript 5.x / Node 20+

**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy 2.x, aiosqlite, Pydantic v2, cachetools
- Frontend: React 18, MUI v6, TanStack Query v5, date-fns, Vite, Vitest, React Testing Library

**Storage**: SQLite via SQLAlchemy 2.x (read-only queries against tables owned by other modules)

**Testing**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend)

**Target Platform**: Linux server (backend), modern browsers Chrome 120+, Firefox 121+, Safari 17+

**Project Type**: Web application — async REST API + React SPA

**Performance Goals**:
- SC-001: Dashboard loads ≤ 2 s for 1,000 owned records
- SC-002: Report page loads ≤ 3 s for 10,000 records, no active filter
- SC-003: Date range / owner filter applied in ≤ 2 s
- SC-004: CSV export of 5,000 rows ≤ 10 s

**Constraints**:
- Read-only module — no writes to source tables
- No external cache store (Redis out of scope); in-process TTL cache only
- Soft-deleted records included in historical aggregates (FR-011)
- SLA data cache TTL: 60 s; all other reports: 300 s

**Scale/Scope**: ≤ 1,000 concurrent users; up to 10,000 source records per report; ≤ 5,000 rows per CSV export

---

## Constitution Check

### Pre-Design Gate

| Principle | Status | Evidence |
|-----------|--------|---------|
| I. Coding Standards | ✅ PASS | PEP 8 + Ruff; TypeScript strict; ESLint Airbnb |
| II. SOLID | ✅ PASS | `ReportQueryBuilder`, `CacheManager`, `DashboardService`, `CSVStreamer` — each single-responsibility; `IReportRepository` abstract base |
| III. DRY | ✅ PASS | Role-scope injection in one `ReportQueryBuilder.with_role_scope()` method; single `ReportTable` React component reused across all three report pages |
| IV. Security First | ✅ PASS | Role scope enforced at service layer before query construction; Sales Rep `owner_id` forced to caller; no direct SQL string interpolation |
| V. UX | ✅ PASS | Deactivated user label `"(deactivated)"` in MUI DataGrid; loading skeleton on report page; filter panel accessible via keyboard |

**Constitution Check: PASS — proceed to Phase 1.**

### Post-Design Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| II. SOLID — O/C | ✅ PASS | New widget types added via `WidgetRegistry.register()` without modifying `DashboardService` |
| III. DRY | ✅ PASS | Archive-inclusion handled once in `BaseReportQuery._apply_archive_policy()` |
| IV. Security | ✅ PASS | `owner_id` override for non-privileged roles rejected at route-level dependency |

---

## Project Structure

### Documentation (this feature)

```text
specs/004-analytics-reporting/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── api.md           ← Phase 1 output
└── tasks.md             ← Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   └── (no new tables — reads from existing ORM models)
│   ├── schemas/
│   │   └── analytics.py                # Pydantic v2: DashboardResponse, SalesReportResponse, etc.
│   ├── repositories/
│   │   └── analytics_repository.py     # Raw async SQL aggregates (read-only)
│   ├── services/
│   │   ├── dashboard_service.py        # asyncio.gather() widget queries per role
│   │   ├── report_query_builder.py     # Role-scoped query construction + filter application
│   │   ├── cache_manager.py            # TTLCache wrapper (5 min / 1 min); CacheInvalidator
│   │   └── csv_streamer.py             # StreamingResponse CSV writer (500-row chunks)
│   └── api/
│       └── v1/
│           ├── analytics_dashboard.py
│           ├── analytics_sales.py
│           ├── analytics_support.py
│           └── analytics_contracts.py
└── tests/
    ├── unit/
    │   ├── test_report_query_builder.py
    │   ├── test_cache_manager.py
    │   └── test_csv_streamer.py
    └── integration/
        ├── test_dashboard_api.py
        ├── test_sales_report_api.py
        ├── test_support_report_api.py
        └── test_contract_report_api.py

frontend/
├── src/
│   ├── types/
│   │   └── analytics.ts               # DashboardWidget, SalesReport, SupportReport, ContractReport
│   ├── services/
│   │   └── analyticsApi.ts            # Axios wrappers; CSV export trigger
│   ├── hooks/
│   │   └── useAnalytics.ts            # TanStack Query hooks, staleTime per cache TTL
│   ├── components/
│   │   └── analytics/
│   │       ├── DashboardWidget.tsx     # Single metric tile (icon + value + label)
│   │       ├── DashboardGrid.tsx       # Responsive MUI Grid of DashboardWidget tiles
│   │       ├── ReportFilterBar.tsx     # Date range picker + owner filter (role-aware)
│   │       ├── ReportTable.tsx         # Reusable MUI DataGrid for all report types
│   │       ├── CacheTimer.tsx          # "Refreshing in X minutes" indicator
│   │       └── ExportButton.tsx        # CSV download trigger with loading state
│   └── pages/
│       ├── DashboardPage.tsx
│       ├── SalesReportPage.tsx
│       ├── SupportReportPage.tsx
│       └── ContractReportPage.tsx
└── tests/
    ├── Dashboard.test.tsx
    ├── SalesReport.test.tsx
    ├── SupportReport.test.tsx
    └── ContractReport.test.tsx
```

**Structure Decision**: Web application (Option 2) — consistent with Module 008 and 003.

---

## Key Design Decisions

### Report Query Builder

```python
class ReportQueryBuilder:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._owner_id: int | None = None

    def with_role_scope(self, user: User) -> "ReportQueryBuilder":
        if user.role in (Role.SALES_REP, Role.SUPPORT_AGENT):
            self._owner_id = user.id
        return self

    def with_date_range(self, after: date, before: date) -> "ReportQueryBuilder": ...
    def build_sales_report(self) -> Select: ...
    def build_support_report(self) -> Select: ...
    def build_contract_report(self) -> Select: ...
```

### Cache Manager

```python
class CacheManager:
    _caches: dict[str, TTLCache] = {
        "support": TTLCache(maxsize=256, ttl=60),
        "default": TTLCache(maxsize=1024, ttl=300),
    }

    async def get_or_set(self, key: ReportCacheKey, factory: Callable) -> Any:
        cache = self._caches.get(key.report_type, self._caches["default"])
        async with self._lock:
            if key not in cache:
                cache[key] = await factory()
        return cache[key]
```

### Dashboard Parallelism

```python
class DashboardService:
    async def get_widgets(self, user: User) -> list[WidgetResult]:
        widget_fns = WIDGET_REGISTRY.for_role(user.role)
        results = await asyncio.gather(*[fn(user, self._session) for fn in widget_fns])
        return [r for r in results if r is not None]
```

### React TanStack Query Configuration

```typescript
const useSalesReport = (filters: ReportFilters) =>
  useQuery({
    queryKey: ['report', 'sales', filters],
    queryFn: () => analyticsApi.getSalesReport(filters),
    staleTime: 4 * 60 * 1000,  // refresh before 5-min server cache expires
    gcTime: 10 * 60 * 1000,
  });

const useSupportReport = (filters: ReportFilters) =>
  useQuery({
    queryKey: ['report', 'support', filters],
    queryFn: () => analyticsApi.getSupportReport(filters),
    staleTime: 50 * 1000,      // refresh before 1-min SLA cache expires
  });
```

---

## Complexity Tracking

> No constitution violations — table left empty intentionally.
