# Research: Analytics & Reporting (Module 004)

**Date**: 2026-06-16 | **Feature**: 004-analytics-reporting

---

## 1. Report Aggregation Strategy

**Decision**: SQL aggregate queries executed at request time, cached in-process with `asyncio`-safe TTL cache (`cachetools.TTLCache` wrapped in an async lock); 5-minute TTL for most reports, 1-minute TTL for SLA data.

**Rationale**: SQLite WAL mode supports concurrent reads; aggregate queries over up to 10,000 records (SC-002) run in < 200 ms with proper indexes. An in-process TTL cache keyed by `(report_type, role, owner_id, filters_hash)` avoids re-running identical queries. The 1-minute SLA exception is handled by a separate cache instance with shorter TTL. No external cache (Redis) needed for MVP scale.

**Alternatives considered**: Materialised view table refreshed by APScheduler (crash-safe but adds write amplification and schema complexity); no cache / always live (violates FR-008 5-minute cache requirement at scale); Redis (external dependency, out of scope).

---

## 2. Role-Scoped Data Access

**Decision**: `ReportQueryBuilder` class injects a `WHERE owner_id = :user_id` clause for Sales Rep / Support Agent; omits the clause for Manager / Admin. The role check happens in the service layer before query construction.

**Rationale**: Role scoping is a hard correctness requirement (SC-005: zero bypass paths). Embedding scope in query construction (not in post-filter Python) ensures the DB enforces it. A single `ReportQueryBuilder` class with a `with_role_scope(user)` method keeps the logic in one place (DRY).

**Alternatives considered**: Row-level security (not supported by SQLite); application-level post-filter (risk of off-by-one in pagination, harder to audit); separate views per role (schema explosion).

---

## 3. CSV Export

**Decision**: Streaming `StreamingResponse` with `csv` stdlib writer; yields rows in chunks of 500. Query is the same scoped aggregate query used for the report, with no pagination limit.

**Rationale**: CSV export of up to 5,000 rows must complete in ≤ 10 s (SC-004). Streaming avoids holding the full result set in memory. The same role-scoped query builder ensures exported data matches what the user sees in the UI. File is streamed directly; no temp file on disk.

**Alternatives considered**: Celery task for async export with download link (adds broker dependency, overkill for 5,000 rows); pandas (heavy dependency, unnecessary for simple CSV).

---

## 4. Dashboard Widget Architecture

**Decision**: Each `DashboardWidget` is a lightweight aggregate query mapped to a `WidgetType` enum. Dashboard config is a static per-role mapping (not user-configurable in v1).

**Rationale**: The dashboard must load in ≤ 2 s (SC-001) for users with up to 1,000 owned records. Each widget runs a single aggregate query (COUNT, SUM, MAX). Queries are parallelised with `asyncio.gather()` at the service layer. Widget config-as-code avoids a configuration table for v1.

**Alternatives considered**: Chart library (Recharts/Chart.js) — deferred; spec says tabular only for v1. User-configurable widgets — out of scope v1.

---

## 5. Date/Time Zone Handling

**Decision**: All DB datetimes stored as UTC. API responses include UTC ISO8601 strings. Frontend converts to the user's configured time zone using `Intl.DateTimeFormat` with the `timeZone` from the user's profile (Module 006).

**Rationale**: Server-side TZ conversion is fragile (DST edge cases, user session state). Storing UTC and converting in the browser is the standard approach. The user's time zone string (e.g., `"America/New_York"`) is read from the auth context and applied via `date-fns-tz` or native `Intl` API.

**Alternatives considered**: Server-side conversion (risky for DST transitions, hard to test); epoch integers (poor DX for date-range filters).

---

## 6. Report Caching Cache Invalidation

**Decision**: Cache key includes a `version` counter per report type, incremented by `CacheInvalidator.invalidate(report_type)` whenever source data changes (ticket status change, deal update, contract update). `CacheInvalidator` is called by the relevant service modules.

**Rationale**: Time-based TTL alone could serve stale data for up to 5 minutes after a bulk operation. Adding version-based invalidation allows a status change to immediately expire the Support Report cache. The version counter is an in-process integer — resets on restart (acceptable; TTL will expire naturally).

**Alternatives considered**: Event bus for cache invalidation (over-engineered for MVP); no invalidation / pure TTL (acceptable for most reports, problematic for SLA).

---

## 7. Soft-Delete / Archived Record Inclusion

**Decision**: All report queries include archived records by default (no `WHERE deleted_at IS NULL`). Archived records are flagged with an `(archived)` label in detail views.

**Rationale**: FR-011 requires archived deals, tickets, and contracts to be included in historical aggregates. The `deleted_at IS NULL` filter is only applied to *active list* views (not report aggregates). This is enforced at the query builder level, not left to callers.

**Alternatives considered**: Separate archive tables (migration complexity, joins across tables); caller-controlled include-archived flag (risk of incorrect default).
