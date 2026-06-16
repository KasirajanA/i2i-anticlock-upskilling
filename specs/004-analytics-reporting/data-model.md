# Data Model: Analytics & Reporting (Module 004)

**Date**: 2026-06-16 | **Feature**: 004-analytics-reporting

---

## Design Note

The Analytics module is **read-only** — it does not own any tables. All aggregations are computed against tables owned by other modules:

| Source Table | Owned By |
|---|---|
| `deals` | 002-sales-pipeline |
| `tickets`, `sla_records` | 003-customer-support |
| `contracts` | 001-contract-management |
| `users` | 005-authentication / 006-user-team-management |
| `accounts` | 007-contact-management |

---

## Report Query Definitions (virtual / in-code)

The following are documented as logical models for the data that each report aggregates. No new tables are created by this module.

---

### DashboardWidget (virtual)

A role-specific metric tile. Computed at request time via a single aggregate query.

| Widget Key | Role(s) | Source | Aggregation |
|---|---|---|---|
| `open_deals_count` | Sales Rep, Admin | `deals` | `COUNT(*) WHERE status != 'closed' AND owner_id = :me` |
| `pipeline_value` | Sales Rep, Admin | `deals` | `SUM(value) WHERE status NOT IN ('won','lost','closed')` |
| `deals_closing_this_month` | Sales Rep, Admin | `deals` | `COUNT(*) WHERE close_date BETWEEN month_start AND month_end` |
| `overdue_deals` | Sales Rep, Admin | `deals` | `COUNT(*) WHERE close_date < NOW() AND status NOT IN ('won','lost')` |
| `open_tickets` | Support Agent, Admin | `tickets` | `COUNT(*) WHERE status IN ('open','in_progress')` |
| `sla_breach_count` | Support Agent, Admin | `sla_records` | `COUNT(*) WHERE (first_response_breached OR resolution_breached) AND is_active` |
| `resolved_this_week` | Support Agent, Admin | `tickets` | `COUNT(*) WHERE status='resolved' AND resolved_at > week_start` |
| `org_open_deals` | Manager, Admin | `deals` | org-wide, no owner filter |
| `org_open_tickets` | Manager, Admin | `tickets` | org-wide |
| `contracts_expiring_soon` | Manager, Admin | `contracts` | `COUNT(*) WHERE expiry_date BETWEEN NOW() AND NOW()+30d` |
| `total_active_accounts` | Manager, Admin | `accounts` | `COUNT(*) WHERE deleted_at IS NULL` |

---

### SalesReport (virtual)

Aggregation of `deals` table.

| Dimension | Metric |
|---|---|
| Stage breakdown | `COUNT(*)`, `SUM(value)` grouped by `stage` |
| Won/Lost | `COUNT(*) WHERE outcome IN ('won','lost')` for date range |
| Average deal value | `AVG(value)` for closed deals in range |
| Top reps by revenue | `SUM(value) WHERE outcome='won'` grouped by `owner_id`, ordered DESC, top 10 |

**Filters**: `created_after`, `created_before`, `owner_id` (Sales Rep sees only their own; Manager/Admin see all)

---

### SupportReport (virtual)

Aggregation of `tickets` and `sla_records`.

| Dimension | Metric |
|---|---|
| Status breakdown | `COUNT(*)` grouped by `status` |
| Priority breakdown | `COUNT(*)` grouped by `priority` |
| Avg resolution time | `AVG(resolved_at - created_at)` for resolved tickets |
| SLA breach rate | `COUNT(breached) / COUNT(total)` for active SLA records |
| Per-agent counts | `COUNT(*)` grouped by `assignee_id` |

**Filters**: `created_after`, `created_before`, `assignee_id` (Support Agent sees only their own)

**Cache TTL**: 1 minute (SLA data freshness requirement)

---

### ContractReport (virtual)

Aggregation of `contracts` table.

| Dimension | Metric |
|---|---|
| Status breakdown | `COUNT(*)`, `SUM(value)` grouped by `status` |
| Upcoming renewals | `COUNT(*)` WHERE `expiry_date BETWEEN NOW() AND NOW()+{window}d` |
| Value by account | `SUM(value)` grouped by `account_id` |

**Filters**: `renewal_window` (30/60/90 days), `owner_id` (Sales Rep sees only their own)

---

## Cache Model (in-process, not persisted)

```python
@dataclass
class ReportCacheKey:
    report_type: str        # 'sales' | 'support' | 'contract' | 'dashboard'
    role: str
    owner_id: int | None    # None for Manager/Admin (org-wide)
    filters_hash: str       # SHA-256 of serialised filter params
    version: int            # Incremented by CacheInvalidator on source data change
```

**TTL**:
- `support` report: 60 seconds
- All other reports and dashboard: 300 seconds

---

## Validation Rules

- Date range: `created_after` must be before `created_before`; max range 366 days
- `renewal_window`: must be one of `30`, `60`, `90`
- `owner_id` filter: Sales Rep / Support Agent — forced to caller's own ID (cannot request other users' data)
- `limit` for CSV export: no limit (scoped by role); frontend enforces ≤ 5,000 row soft warning
