# Feature Specification: Analytics & Reporting

**Feature Branch**: `004-analytics-reporting`

**Created**: 2026-06-15

**Status**: Draft

**Input**: User description: "CRM application — Analytics & Reporting module (dashboards, pipeline reports, support reports, contract reports, role-scoped data)."

## Clarifications

### Session 2026-06-16

- Q: Is "Manager" a separate formal role or equivalent to Admin? → A: Separate role — org-wide report/dashboard access, no system-admin capabilities.
- Q: What happens to report data when a source record is permanently deleted? → A: Soft delete only — permanent deletion of deals, tickets, and contracts is disallowed; records are archived.
- Q: Is CSV export available to all roles or restricted to Managers/Admins? → A: All roles — each exports only their own scoped data, bounded by FR-005 role scoping.
- Q: Does the 5-minute cache apply to SLA data in the Support Report? → A: No — Support Report SLA data refreshes every 1 minute; all other reports keep the 5-minute cache.
- Q: Do Managers see full org-wide data or only their team's data? → A: Full org-wide data — no team scoping in v1.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Personal Dashboard (Priority: P1)

A logged-in user lands on a dashboard showing key metrics relevant to their role: a Sales
Rep sees their open deals and pipeline value; a Support Agent sees their open ticket count
and SLA health; an Admin sees organisation-wide summaries of all modules.

**Why this priority**: The dashboard is the first screen users see after login; it must
immediately surface actionable data.

**Independent Test**: Log in as a Sales Rep with 3 open deals; confirm the dashboard shows
the correct deal count, total pipeline value, and number of overdue deals. Repeat for a
Support Agent.

**Acceptance Scenarios**:

1. **Given** a Sales Rep logs in, **When** the dashboard loads, **Then** they see their open
   deal count, total pipeline value, deals closing this month, and overdue deals.
2. **Given** a Support Agent logs in, **When** the dashboard loads, **Then** they see their
   open ticket count, SLA breach count, and tickets resolved this week.
3. **Given** an Admin logs in, **When** the dashboard loads, **Then** they see
   organisation-wide totals: all open deals, all open tickets, contracts expiring soon, and
   total active accounts.

---

### User Story 2 - Sales Pipeline Report (Priority: P1)

A Manager or Admin opens the Sales Report and sees deal totals by stage, won/lost ratio for
a selected period, average deal value, and top-performing reps by closed revenue.

**Why this priority**: Pipeline reports are the primary management tool for understanding
sales health and forecasting revenue.

**Independent Test**: Create a set of deals with known values, stages, and outcomes across
two reps; open the Sales Report, apply a date filter for the current month, and verify all
aggregated totals match expected values.

**Acceptance Scenarios**:

1. **Given** a Manager on the Sales Report, **When** the report loads, **Then** they see
   total deal value by stage, won/lost counts, and average deal value for the selected period.
2. **Given** a date range filter applied, **When** confirmed, **Then** all report metrics
   update to reflect only deals with close dates in that range.
3. **Given** a Sales Rep on the Sales Report, **When** it loads, **Then** they see only their
   own deal data — not other reps' figures.

---

### User Story 3 - Support Performance Report (Priority: P1)

A Manager or Admin opens the Support Report and sees ticket volume by status and priority,
average resolution time, SLA breach rate, and per-agent ticket counts.

**Why this priority**: Support managers need objective data to assess team performance and
identify SLA problem areas.

**Independent Test**: Create tickets with known statuses, priorities, and resolution times;
open the Support Report and verify counts and average resolution time match expected values.

**Acceptance Scenarios**:

1. **Given** a Manager on the Support Report, **When** it loads, **Then** they see ticket
   counts by status (Open, In Progress, Resolved, Closed) and by priority.
2. **Given** a date range applied, **When** confirmed, **Then** metrics reflect only tickets
   created within that range.
3. **Given** a Support Agent viewing the report, **When** it loads, **Then** they see only
   metrics for their own assigned tickets.

---

### User Story 4 - Contract Expiry Report (Priority: P2)

An Admin or Sales Rep opens the Contract Report and sees contracts grouped by status,
upcoming renewals within the next 30/60/90 days, and total contract value by account.

**Why this priority**: Contract visibility prevents revenue leakage from unnoticed expirations.

**Independent Test**: Create contracts expiring at 15, 45, and 100 days from today; open the
Contract Report with the 60-day renewal filter and confirm only the first two appear.

**Acceptance Scenarios**:

1. **Given** an Admin on the Contract Report, **When** it loads, **Then** they see all
   contracts grouped by status with total value per group.
2. **Given** a renewal window filter (30/60/90 days), **When** selected, **Then** only
   contracts expiring within that window are shown.
3. **Given** a Sales Rep on the Contract Report, **When** it loads, **Then** they see only
   contracts they own.

---

### Edge Cases

- What happens to historical report data when a user is deactivated?
- How are reports affected when a deal or ticket is permanently deleted?
- What is the data freshness guarantee — are reports real-time or cached?
- How are timezone differences handled in date-range filters (user's timezone vs. server)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every user MUST see a role-specific dashboard on login showing metrics
  relevant to their role (see User Story 1 for role matrix).
- **FR-002**: Sales Report MUST show: deal count and value by stage, won/lost counts and
  ratio, average deal value, and top reps by closed revenue — filterable by date range and
  owner.
- **FR-003**: Support Report MUST show: ticket counts by status and priority, average
  resolution time, SLA breach rate, and per-agent ticket counts — filterable by date range
  and agent.
- **FR-004**: Contract Report MUST show: contracts grouped by status with total value,
  upcoming renewals filterable by 30/60/90-day window, and value by account — filterable
  by owner.
- **FR-005**: Sales Reps and Support Agents MUST see only their own data in all reports;
  Managers and Admins MUST see full organisation-wide data with owner/agent filter controls.
  Manager is a distinct role with org-wide read access to all reports and dashboards but no
  system-admin capabilities. Team-scoped Manager access is out of scope for v1.
- **FR-006**: All reports MUST support date range filtering; default range is current
  calendar month.
- **FR-007**: Reports MUST be exportable to CSV for the visible filtered data set. All roles
  may export; the exported data is scoped to the same records the user can view per FR-005.
- **FR-008**: Dashboard metrics MUST refresh when the user reloads the page. Report pages
  MAY cache aggregations for up to 5 minutes to reduce database load, with one exception:
  SLA-related data in the Support Report MUST refresh within 1 minute to maintain alignment
  with SLA breach detection guarantees.
- **FR-009**: All report date/time values MUST render in the viewing user's configured time
  zone.
- **FR-010**: Deactivated users' historical data MUST remain in reports; their name is shown
  with a "(deactivated)" indicator.
- **FR-011**: Permanent deletion of deals, tickets, and contracts is disallowed system-wide;
  records MUST be archived (soft-deleted) to preserve report aggregate integrity. Reports
  MUST include archived records in historical aggregates.

### Key Entities

- **DashboardWidget**: A metric tile on the personal dashboard, scoped to the user's role
  and owned data.
- **SalesReport**: Aggregated view of deal data with stage, value, and outcome dimensions.
- **SupportReport**: Aggregated view of ticket data with status, priority, SLA, and
  per-agent dimensions.
- **ContractReport**: Aggregated view of contract data with status, value, and renewal
  timeline dimensions.
- **ReportFilter**: Date range, owner/agent, and module-specific filter parameters applied
  to a report.
- **Manager**: A formal system role distinct from Admin — full org-wide read access to all
  reports and dashboards; cannot modify system configuration or user permissions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dashboard loads within 2 seconds for any role with up to 1,000 owned records.
- **SC-002**: Report pages load within 3 seconds for data sets up to 10,000 records with no
  active filter.
- **SC-003**: Applying a date range or owner filter updates report results within 2 seconds.
- **SC-004**: CSV export of up to 5,000 rows completes within 10 seconds.
- **SC-005**: Role scoping is 100% accurate — zero instances of a Sales Rep or Support Agent
  seeing another user's data, validated by role-matrix testing before launch.
- **SC-006**: Report metrics match source record counts exactly — zero aggregation errors
  validated by test data with known totals.

## Assumptions

- Reports are read-only; users cannot edit source records from within a report view.
- Data freshness: dashboard metrics are live on page load; report pages cache aggregations
  for up to 5 minutes to reduce database load.
- Custom report builder (ad-hoc queries, custom dimensions) is out of scope for v1; only
  the four predefined reports are included.
- CSV export includes all columns visible in the filtered report at the time of export.
- Charts and graphs are out of scope for v1; all reports display data in tabular format only.
- Historical data for deactivated users is preserved and included in reports; it is never
  purged.
- Manager is a distinct system role with full org-wide read access to all reports and
  dashboards; Managers have no system-admin capabilities. Team-scoped access is out of scope
  for v1.
- Permanent deletion of deals, tickets, and contracts is disallowed; soft-delete (archive)
  is the only supported removal mechanism to preserve report aggregate integrity.
- CSV export is available to all roles; exported data is scoped identically to the user's
  report view per FR-005.
- Support Report SLA data has a maximum cache age of 1 minute; all other report pages cache
  aggregations for up to 5 minutes.
- Reports affected when a source record is archived: archived records are included in
  historical aggregates and marked as archived where record-level detail is shown.
