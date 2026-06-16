# API Contract: Analytics & Reporting (Module 004)

**Base path**: `/api/v1/analytics`  
**Auth**: Bearer token required on all endpoints  
**Content-Type**: `application/json` (except CSV export which is `text/csv`)

---

## Dashboard

### `GET /api/v1/analytics/dashboard`

Returns role-specific metric widgets for the authenticated user.

**Response 200**
```json
{
  "role": "sales_rep",
  "widgets": [
    { "key": "open_deals_count",       "label": "Open Deals",           "value": 12,        "unit": "deals" },
    { "key": "pipeline_value",          "label": "Pipeline Value",       "value": 240000.00, "unit": "USD" },
    { "key": "deals_closing_this_month","label": "Closing This Month",   "value": 3,         "unit": "deals" },
    { "key": "overdue_deals",           "label": "Overdue Deals",        "value": 1,         "unit": "deals" }
  ],
  "generated_at": "2026-06-16T09:00:00Z"
}
```

**Behaviour**: Widgets set is determined server-side by the caller's role. Sales Rep sees own-data widgets; Manager/Admin sees org-wide widgets. Response is live (not cached) — refreshes on page load per FR-008.

---

## Sales Report

### `GET /api/v1/analytics/reports/sales`

**Query parameters**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `created_after` | ISO8601 date | start of current month | Date range start |
| `created_before` | ISO8601 date | end of current month | Date range end |
| `owner_id` | integer | caller's ID (for Sales Rep) | Filter by deal owner; Sales Rep cannot change this |

**Response 200**
```json
{
  "stage_breakdown": [
    { "stage": "prospecting", "count": 10, "total_value": 50000.00 },
    { "stage": "proposal",    "count": 5,  "total_value": 120000.00 }
  ],
  "won_count": 3,
  "lost_count": 2,
  "won_lost_ratio": 1.5,
  "average_deal_value": 34500.00,
  "top_reps": [
    { "user_id": 5, "display_name": "Alice Smith", "closed_revenue": 95000.00 }
  ],
  "filters_applied": {
    "created_after": "2026-06-01",
    "created_before": "2026-06-30",
    "owner_id": null
  },
  "cached_until": "2026-06-16T09:05:00Z"
}
```

**Errors**: 403 if Sales Rep requests `owner_id` of another user.

---

### `GET /api/v1/analytics/reports/sales/export`

**Query parameters**: Same as the report endpoint.

**Response 200** — `Content-Type: text/csv`, `Content-Disposition: attachment; filename="sales-report-2026-06.csv"`

```csv
deal_id,title,owner,stage,value,outcome,close_date
1,Acme Deal,Alice Smith,won,45000,won,2026-06-10
...
```

Streaming response; rows limited to caller's role scope.

---

## Support Report

### `GET /api/v1/analytics/reports/support`

**Query parameters**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `created_after` | ISO8601 date | start of current month | |
| `created_before` | ISO8601 date | end of current month | |
| `assignee_id` | integer | caller's ID (for Support Agent) | |

**Response 200**
```json
{
  "status_breakdown": [
    { "status": "open",        "count": 42 },
    { "status": "in_progress", "count": 18 },
    { "status": "resolved",    "count": 91 },
    { "status": "closed",      "count": 230 }
  ],
  "priority_breakdown": [
    { "priority": "critical", "count": 3 },
    { "priority": "high",     "count": 25 }
  ],
  "avg_resolution_hours": 18.4,
  "sla_breach_rate": 0.07,
  "per_agent_counts": [
    { "user_id": 7, "display_name": "Bob Jones", "ticket_count": 34, "breach_count": 2 }
  ],
  "filters_applied": { "created_after": "2026-06-01", "created_before": "2026-06-30", "assignee_id": null },
  "cached_until": "2026-06-16T09:01:00Z"
}
```

**Note**: `cached_until` for support report is 1 minute from generation (not 5 minutes).

---

### `GET /api/v1/analytics/reports/support/export`

Same as sales export; returns ticket-level rows scoped to caller's role.

---

## Contract Report

### `GET /api/v1/analytics/reports/contracts`

**Query parameters**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `renewal_window` | integer | 30 | Days ahead: `30`, `60`, or `90` |
| `owner_id` | integer | caller's ID (for Sales Rep) | |

**Response 200**
```json
{
  "status_breakdown": [
    { "status": "active",   "count": 45, "total_value": 890000.00 },
    { "status": "expiring", "count": 8,  "total_value": 130000.00 },
    { "status": "expired",  "count": 12, "total_value": 210000.00 }
  ],
  "upcoming_renewals": [
    { "contract_id": 3, "account_name": "Acme Corp", "value": 24000.00, "expiry_date": "2026-07-10", "days_remaining": 24 }
  ],
  "value_by_account": [
    { "account_id": 5, "account_name": "Globex", "total_value": 120000.00 }
  ],
  "filters_applied": { "renewal_window": 30, "owner_id": null },
  "cached_until": "2026-06-16T09:05:00Z"
}
```

---

### `GET /api/v1/analytics/reports/contracts/export`

Returns contract-level rows in CSV, scoped to caller's role.

---

## Error Responses

```json
{
  "type": "https://crm.i2i.io/errors/access-denied",
  "title": "Access Denied",
  "status": 403,
  "detail": "Sales representatives cannot view other users' report data."
}
```

| Status | Meaning |
|--------|---------|
| 401 | Missing or expired session |
| 403 | Role scope violation (Sales Rep requesting other user's data) |
| 422 | Invalid filter parameters (invalid date range, unsupported renewal window) |
| 500 | Internal server error |
