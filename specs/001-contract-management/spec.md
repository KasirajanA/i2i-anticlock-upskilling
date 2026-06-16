# Feature Specification: Contract Management

**Feature Branch**: `001-contract-management`

**Created**: 2026-06-15

**Status**: Draft

**Input**: User description: "CRM application — Contract Management module (create, manage, and track contracts linked to accounts and deals)."

## Clarifications

### Session 2026-06-15

- Q: Can users attach files to a contract (e.g., a signed PDF or supporting document)? → A: Yes — one file attachment per contract, stored internally.
- Q: Can a Sales Rep edit a contract they do not own? → A: No — Sales Reps edit only their own contracts; Admins and Managers can edit any.
- Q: How are contract IDs formatted for display and external reference? → A: Auto-generated sequential number with prefix — e.g., CON-0001, CON-0002.
- Q: Which backward lifecycle transitions can Admins perform? → A: Admins can revert to any previous state, including from Expired and Terminated.
- Q: Via which channel is the contract owner notified for Renewal Due and Expiry events? → A: In-app notification only (web app); email is out of scope for v1.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a Contract (Priority: P1)

A Sales Rep creates a new contract, links it to an existing account and optionally a deal,
fills in the key terms (value, start date, end date, description), and saves it as a Draft.

**Why this priority**: Contract creation is the entry point of the contract lifecycle; all
other stories depend on a contract existing.

**Independent Test**: Create a contract linked to a test account, verify it appears in the
contract list with "Draft" status and the correct linked account name.

**Acceptance Scenarios**:

1. **Given** a Sales Rep, **When** they submit a new contract with account, value, start date,
   and end date, **Then** the contract is saved with status "Draft" and appears in the list.
2. **Given** a missing required field (account or end date), **When** the form is submitted,
   **Then** inline validation highlights the missing field and blocks submission.
3. **Given** a start date later than the end date, **When** submitted, **Then** a validation
   error prevents saving.

---

### User Story 2 - Manage Contract Lifecycle (Priority: P1)

A Sales Rep or Admin moves a contract through its lifecycle: Draft → Sent for Review →
Active → Expired/Terminated. Each transition is logged with a timestamp and the acting user.

**Why this priority**: The lifecycle status is the primary indicator of a contract's health
and drives renewal and support workflows.

**Independent Test**: Create a Draft contract, advance it to Active, then to Expired — confirm
each status change appears in the contract's activity log with the correct timestamp.

**Acceptance Scenarios**:

1. **Given** a Draft contract, **When** a user marks it as "Sent for Review", **Then** the
   status updates and the change is logged.
2. **Given** a "Sent for Review" contract, **When** marked Active, **Then** the contract
   appears in the Active Contracts list.
3. **Given** a contract whose end date has passed, **When** the system checks daily,
   **Then** it is automatically moved to "Expired" and the contract owner is notified.
4. **Given** an Active contract, **When** a user terminates it early with a reason, **Then**
   the status changes to "Terminated" and the reason is stored.

---

### User Story 3 - Renewal Tracking (Priority: P2)

Thirty days before a contract's end date, the contract owner receives a notification and the
contract is flagged "Renewal Due" in the list view. The owner can then renew (creating a
successor contract) or let it expire.

**Why this priority**: Missed renewals are a direct revenue risk; proactive flagging prevents
silent churn.

**Independent Test**: Set a contract end date to 29 days from today, confirm it is flagged
"Renewal Due" in the list and the owner has received a notification.

**Acceptance Scenarios**:

1. **Given** a contract expiring in ≤ 30 days, **When** the daily renewal check runs,
   **Then** the contract is flagged "Renewal Due" and the owner is notified.
2. **Given** a "Renewal Due" contract, **When** the owner clicks Renew, **Then** a new Draft
   contract is pre-filled with the same account, value, and terms, with dates advanced by
   one term length.
3. **Given** a renewed contract, **When** viewing the original, **Then** a link to the
   successor contract is visible in the activity log.

---

### User Story 4 - Search & Filter Contracts (Priority: P2)

A user filters the contract list by status, account, owner, or date range to find specific
contracts quickly.

**Why this priority**: As the contract list grows, unfiltered browsing becomes impractical.

**Independent Test**: Create contracts with different statuses and accounts, apply a filter
for "Active" status and a specific account, and confirm only matching contracts are shown.

**Acceptance Scenarios**:

1. **Given** a user on the contract list, **When** they filter by status "Active", **Then**
   only active contracts are shown.
2. **Given** a date range filter applied, **When** confirmed, **Then** only contracts with
   end dates within the range appear.
3. **Given** a combined filter (status + account), **When** applied, **Then** results satisfy
   both conditions simultaneously.

---

### Edge Cases

- What happens when a contract's linked account is archived?
- Can two active contracts exist for the same account simultaneously?
- What happens if the renewal check runs while a contract is being edited?
- How are contracts with no linked deal handled in the pipeline view?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to create contracts with: linked account (required), linked
  deal (optional), contract value, start date, end date, description, owner, and one optional
  file attachment (PDF, DOCX, or image; max 1 MB). Each contract MUST be assigned an
  auto-generated reference ID in the format `CON-NNNN` (e.g., CON-0001) on creation.
- **FR-001a**: A contract MUST support exactly one file attachment at a time; uploading a new
  file replaces the previous one. The replaced file is not retained.
- **FR-002**: Contracts MUST follow a defined lifecycle: Draft → Sent for Review → Active →
  Expired / Terminated. Non-admin users may only advance forward. Admins MAY revert a
  contract to any previous status, including from Expired or Terminated; every such revert
  MUST be logged with the acting Admin's identity and a mandatory reason.
- **FR-003**: All status transitions MUST be logged in the contract's activity log with
  timestamp and acting user.
- **FR-004**: System MUST automatically transition contracts to "Expired" when their end date
  passes (checked daily).
- **FR-005**: System MUST flag contracts as "Renewal Due" when the end date is within 30 days
  and deliver an in-app notification to the contract owner when they are logged in. Email
  notifications are out of scope for v1.
- **FR-006**: Users MUST be able to renew a contract, pre-filling a new Draft from the
  existing contract's details.
- **FR-007**: Users MUST be able to terminate an Active contract early by providing a reason.
- **FR-008**: Contract list MUST be filterable by status, account, owner, and end date range.
- **FR-009**: Each contract MUST display a full activity log showing all status changes, edits,
  and linked notifications.
- **FR-010**: Contracts MUST be accessible to Admins and Sales Reps; Support Agents have no
  access to this module.
- **FR-011**: Sales Reps MUST only be able to edit contracts they own; they may view (read-only)
  contracts owned by other reps. Admins and Managers MAY edit any contract.

### Key Entities

- **Contract**: Core record with auto-generated reference ID (`CON-NNNN`), value, dates,
  status, description, owner, links to account and optionally a deal, and an optional single
  file attachment.
- **ContractAttachment**: Metadata record for the attached file (filename, size, MIME type,
  storage reference). At most one per contract.
- **ContractStatus**: Enumerated lifecycle state — Draft, Sent for Review, Active, Expired,
  Terminated.
- **ActivityLog**: Per-contract log of status changes, edits, and system events.
- **RenewalLink**: Association between an original contract and its successor.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A Sales Rep can create a complete contract and save it in under 2 minutes.
- **SC-002**: Automatic expiry transition runs within 24 hours of the contract end date
  passing.
- **SC-003**: Renewal Due flag appears within 24 hours of the contract entering the 30-day
  window.
- **SC-004**: Contract list filtered by any single criterion returns results in under 1 second
  for up to 10,000 contracts.
- **SC-005**: Renewal pre-fill copies all required fields accurately — zero manual re-entry
  needed for identical terms.
- **SC-006**: File attachment upload (up to 1 MB) completes within 2 seconds on a standard
  broadband connection.

## Assumptions

- Contract value is stored as a numeric amount in a single currency; multi-currency support
  is out of scope for v1.
- There is no e-signature integration in v1; "Sent for Review" and "Active" are manually
  advanced by the user.
- A contract may link to at most one deal, but an account may have multiple active contracts
  simultaneously.
- The daily expiry and renewal checks run as a scheduled background job; real-time triggering
  is not required.
- Admins can revert a contract to any previous lifecycle status, including from Expired or
  Terminated; a mandatory reason is required for every backward transition and is stored in
  the activity log.
- Deleted accounts do not cascade-delete their contracts; contracts retain the archived
  account reference for audit purposes.
- Each contract supports exactly one file attachment (PDF, DOCX, or image; max 1 MB);
  uploading a new file replaces the previous one without versioning.
- File attachments are stored internally; no external document storage integration in v1.
