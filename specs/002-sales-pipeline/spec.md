# Feature Specification: Sales Pipeline

**Feature Branch**: `002-sales-pipeline`

**Created**: 2026-06-15

**Status**: Draft

**Input**: User description: "CRM application — Sales Pipeline module (deals, pipeline stages, assignment, win/loss tracking)."

## Clarifications

### Session 2026-06-15

- Q: Should deals have an auto-generated reference ID for display? → A: Yes — auto-generated `DEAL-NNNN` format, consistent with contracts.
- Q: Can a Sales Rep view deals owned by reps in a completely different team? → A: No — Sales Reps see only deals within their own team(s); Admins and Managers see all.
- Q: Who can add comments to a deal's activity log? → A: Any user who can view the deal — owner, teammates, Managers, and Admins.
- Q: What does the forecast view show for Closed Won deals? → A: Won deals appear in a separate "Closed Won" total, excluded from open pipeline totals.
- Q: Should reps receive in-app notifications for deal assignment and overdue deals? → A: Yes — in-app notification on deal assignment and when a deal becomes overdue.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create & Manage a Deal (Priority: P1)

A Sales Rep creates a new deal, links it to an account and optionally a contact, sets a
value and expected close date, and assigns it to themselves or another rep.

**Why this priority**: Deals are the primary revenue-tracking entity; the entire pipeline
view is built from deals.

**Independent Test**: Create a deal linked to a test account with a value and close date,
confirm it appears in the pipeline board under the correct stage, and in the deal list with
the correct owner.

**Acceptance Scenarios**:

1. **Given** a Sales Rep, **When** they submit a new deal with account, value, close date,
   and stage, **Then** the deal is saved and appears on the pipeline board in the correct
   stage column.
2. **Given** a missing required field (account or close date), **When** submitted, **Then**
   inline validation blocks the form.
3. **Given** an existing deal, **When** the rep updates the value or close date, **Then**
   the change is saved and logged in the deal's activity log.

---

### User Story 2 - Move Deals Through Pipeline Stages (Priority: P1)

A Sales Rep drags a deal card from one pipeline stage to the next (e.g., Qualified →
Proposal → Negotiation → Closed Won). Each move is logged automatically.

**Why this priority**: The visual pipeline board is the core daily-use interface for sales
reps; stage progression drives forecasting.

**Independent Test**: Create a deal in "Qualified", drag it to "Proposal", confirm the stage
updates on the board and in the activity log, and that the deal list reflects the new stage.

**Acceptance Scenarios**:

1. **Given** a deal on the pipeline board, **When** a rep moves it to the next stage,
   **Then** the stage updates instantly and the move is logged with timestamp.
2. **Given** a deal moved to "Closed Won", **When** confirmed, **Then** the deal is removed
   from the active pipeline view and appears in the Won deals report.
3. **Given** a deal moved to "Closed Lost", **When** the rep enters a loss reason, **Then**
   the deal is archived with the reason stored and visible in the Lost deals report.

---

### User Story 3 - Pipeline Board View (Priority: P1)

A Sales Rep opens the Pipeline view and sees all their open deals as cards organised into
stage columns. They can filter by owner, account, or close date range to focus the board.

**Why this priority**: The board view is the primary workspace for sales reps; it must be
immediately useful without configuration.

**Independent Test**: Create 3 deals across 3 different stages, open the pipeline board, and
confirm each deal appears in the correct column with name, value, and close date visible.

**Acceptance Scenarios**:

1. **Given** a Sales Rep on the pipeline board, **When** the page loads, **Then** they see
   only their own deals grouped by stage, each showing deal name, account, value, and close
   date.
2. **Given** a manager or Admin, **When** they view the pipeline, **Then** they see all deals
   across all reps, with an owner filter available.
3. **Given** a filter applied for a specific account, **When** active, **Then** only deals
   linked to that account are shown across all stage columns.

---

### User Story 4 - Deal Forecasting Summary (Priority: P2)

A manager opens the forecast view and sees the total pipeline value grouped by stage and
close date month, giving visibility into expected revenue for the current and next quarter.

**Why this priority**: Revenue forecasting is a primary management use case; without it the
pipeline data has limited business value.

**Independent Test**: Create deals with values in different stages and close dates across two
months; open the forecast view and confirm the totals per stage and per month are correct.

**Acceptance Scenarios**:

1. **Given** a manager on the forecast page, **When** the page loads, **Then** they see total
   deal value grouped by pipeline stage for the current quarter.
2. **Given** a date range filter applied, **When** confirmed, **Then** only deals with close
   dates in that range contribute to the totals.
3. **Given** a deal moved to Closed Won or Lost, **When** the forecast is viewed, **Then**
   that deal is excluded from the open pipeline totals.

---

### Edge Cases

- What happens to a deal when its linked account is archived?
- Can a deal exist without a linked contact (account-only deal)?
- What happens to pipeline totals when a deal's value is set to zero?
- How are overdue deals (close date in the past, still open) surfaced?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to create deals with: linked account (required), linked
  contact (optional), deal name, value, expected close date, stage, and owner. Each deal
  MUST be assigned an auto-generated reference ID in the format `DEAL-NNNN` (e.g.,
  DEAL-0001) on creation.
- **FR-002**: Default pipeline stages MUST be: Lead In, Qualified, Proposal, Negotiation,
  Closed Won, Closed Lost. Stages are fixed in v1 (not customisable).
- **FR-003**: Users MUST be able to move deals between stages via the pipeline board; each
  move MUST be logged with timestamp and acting user.
- **FR-004**: Closing a deal as "Closed Lost" MUST require a loss reason before saving.
- **FR-005**: Pipeline board MUST display deal cards with name, linked account, value, and
  close date visible without opening the deal.
- **FR-006**: Sales Reps MUST see only deals belonging to their own team(s) — their own deals
  plus teammates' deals (read-only). Deals from outside their team(s) MUST NOT be visible.
  Admins and Managers MUST see all deals organisation-wide with an owner/team filter.
- **FR-007**: Deal list and board MUST be filterable by owner, account, stage, and close date
  range.
- **FR-008**: Forecast view MUST show two distinct sections: (1) open pipeline — total deal
  value grouped by stage and by close month for a configurable date range; (2) Closed Won
  total — sum of won deal values for the same date range. Closed Lost deals MUST be excluded
  from both sections.
- **FR-009**: Overdue open deals (close date in the past) MUST be visually flagged on the
  board and in the list.
- **FR-010**: Deals MUST maintain a full activity log of stage changes, edits, and comments.
  Any user who can view a deal MUST be able to add a comment; only the comment author or
  an Admin MAY delete a comment.
- **FR-011**: System MUST deliver an in-app notification to a rep when: (1) a deal is assigned
  to them, and (2) a deal they own becomes overdue (close date passes while still open).
  Email notifications are out of scope for v1.

### Key Entities

- **Deal**: Core record with auto-generated reference ID (`DEAL-NNNN`), name, value, stage,
  close date, owner, linked account, optional contact, and status (Open / Won / Lost).
- **PipelineStage**: Fixed enumeration — Lead In, Qualified, Proposal, Negotiation,
  Closed Won, Closed Lost.
- **LossReason**: Free-text reason required when closing a deal as Lost.
- **ActivityLog**: Per-deal log of stage changes, edits, comments, and system events.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A Sales Rep can create a new deal and see it on the pipeline board in under
  90 seconds.
- **SC-002**: Pipeline board loads all open deals within 2 seconds for up to 500 deals per
  user.
- **SC-003**: Dragging a deal to a new stage updates the board instantly (optimistic UI) and
  persists within 1 second.
- **SC-004**: Forecast totals are accurate to the cent — zero rounding or aggregation errors
  validated by test data with known totals.
- **SC-005**: Overdue deals are flagged without any manual action — automatic on page load.

## Assumptions

- Pipeline stages are fixed in v1; custom stages are out of scope.
- Deal value is a single numeric amount in one currency; multi-currency is out of scope.
- A deal belongs to exactly one owner; co-ownership is out of scope for v1.
- Deals linked to archived accounts remain visible in the pipeline; the account name is
  shown with an "Archived" indicator.
- Sales Reps can view (read-only) deals owned by other reps within the same team; deals from
  outside their team(s) are not visible to them. Editing another rep's deal requires Manager
  or Admin role.
- The forecast view is read-only; it does not support manual forecast adjustments.
