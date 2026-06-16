# Quickstart Validation Guide: Analytics & Reporting (Module 004)

**Prerequisites**: Backend running on `http://localhost:8000`, frontend on `http://localhost:5173`. At least one each of: deal (all stages), support ticket (all statuses + an SLA breach), contract (active + expiring), user (all roles). All source data modules (001–003, 007) must be operational.

---

## Setup

```bash
# Backend
cd backend && python -m uvicorn app.main:app --reload

# Seed test data
cd backend && python scripts/seed_analytics_data.py

# Frontend
cd frontend && npm run dev

# Run tests
cd backend && pytest tests/analytics/ -v
cd frontend && npm test -- --testPathPattern=analytics
```

---

## Scenario 1 — Role-Specific Dashboard (FR-001, SC-001)

**Sales Rep view**:
1. Log in as a Sales Rep.
2. Navigate to **Dashboard**.
   - **Expected**: Widgets show *own* open deals, pipeline value, closing-this-month count, overdue count.
   - No tickets, no contracts, no org-wide totals visible.

**Support Agent view**:
1. Log in as a Support Agent.
   - **Expected**: Widgets show open ticket count, SLA breach count, resolved this week.

**Admin view**:
1. Log in as Admin.
   - **Expected**: All org-wide widgets: total open deals, total open tickets, contracts expiring in 30 days, active accounts.

**Performance**: Dashboard loads in ≤ 2 s with 1,000 seeded records.

---

## Scenario 2 — Sales Report with Date Filter (FR-002, FR-006, SC-003)

1. Log in as Manager or Admin. Navigate to **Reports → Sales**.
2. Default view shows current month.
   - **Expected**: Stage breakdown, won/lost counts, average deal value, top 3 reps all populated correctly (cross-reference with seeded data totals).
3. Change date range to previous month. Click **Apply**.
   - **Expected**: Report updates in ≤ 2 s; totals match seeded previous-month data.
4. Log in as Sales Rep. Navigate to **Reports → Sales**.
   - **Expected**: Only own deals appear; `owner_id` filter control is hidden.

---

## Scenario 3 — Support Report SLA Freshness (FR-003, FR-008)

1. Log in as Manager. Open **Reports → Support**.
   - **Expected**: SLA breach rate matches current breach count in the support module.
2. In a second tab, create and breach an SLA on a new Critical ticket (use `POST /api/v1/_test/sla/advance-clock`).
3. Wait up to 1 minute and reload the Support Report.
   - **Expected**: Breach rate has updated (cache TTL ≤ 60 s for SLA data).

---

## Scenario 4 — Contract Renewal Window Filter (FR-004, SC-003)

1. Log in as Admin. Navigate to **Reports → Contracts**.
2. Seed contracts expiring at 15 days, 45 days, and 120 days from today.
3. Select renewal window **30 days**.
   - **Expected**: Only the 15-day contract appears in Upcoming Renewals.
4. Switch to **60 days**.
   - **Expected**: 15-day and 45-day contracts appear; 120-day contract does not.

---

## Scenario 5 — CSV Export (FR-007, SC-004)

1. Log in as Sales Rep. Open **Reports → Sales**.
2. Click **Export CSV**.
   - **Expected**: Download starts within 2 s; file contains only own deals; all visible columns present.
3. Log in as Admin. Export the same report.
   - **Expected**: File contains all users' deals.
4. Export with 5,000+ seeded rows — should complete in ≤ 10 s.

---

## Scenario 6 — Role Scope Enforcement (FR-005, SC-005)

1. As Sales Rep, attempt `GET /api/v1/analytics/reports/sales?owner_id=999` (another user's ID).
   - **Expected**: HTTP 403 — "Sales representatives cannot view other users' report data."
2. As Manager, the same request should return org-wide data ignoring the owner_id filter.

---

## Scenario 7 — Deactivated User Data Preservation (FR-010)

1. Create deals owned by User A. Deactivate User A (Module 006).
2. Open Sales Report as Manager.
   - **Expected**: User A's deals appear with the name `"Alice Smith (deactivated)"`.

---

## Unit Test Checklist

| Test File | Coverage |
|-----------|----------|
| `tests/unit/test_report_query_builder.py` | Role scoping, date range injection, filter hash |
| `tests/unit/test_cache_manager.py` | TTL expiry, version invalidation, concurrent reads |
| `tests/unit/test_csv_streamer.py` | Row chunking, column ordering, role scope |
| `tests/integration/test_dashboard_api.py` | Widget values per role, live (no cache) |
| `tests/integration/test_sales_report_api.py` | Stage breakdown, date filter, export |
| `tests/integration/test_support_report_api.py` | Status/priority breakdown, 1-min cache TTL |
| `tests/integration/test_contract_report_api.py` | Renewal window filter, value by account |
| `frontend/tests/Dashboard.test.tsx` | Widget rendering per role mock |
| `frontend/tests/SalesReport.test.tsx` | Filter controls, table data, export button |
