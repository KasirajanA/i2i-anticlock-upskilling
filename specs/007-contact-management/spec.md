# Feature Specification: Contact & Account Management

**Feature Branch**: `007-contact-management`

**Created**: 2026-06-15

**Status**: Draft

**Input**: User description: "CRM application — Contact & Account Management module (contacts, accounts/companies, leads)"

## Clarifications

### Session 2026-06-16

- Q: What happens to a contact when all its linked accounts are archived? → A: Contacts remain active; the archived account is shown with an "(archived)" indicator on the contact record.
- Q: Is contact email required or optional? → A: Required — must be present and valid on every contact; duplicate detection always runs on save.
- Q: What is the full lead status lifecycle? → A: New → Contacted → Qualified → Converted / Disqualified.
- Q: What duplicate-resolution options does CSV bulk import offer? → A: Skip duplicate (default) or Overwrite existing — user selects per import run.
- Q: Which roles can create and manage leads? → A: Sales Rep creates and manages leads; Admin and Manager have read access; Support Agent has no access.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create & Manage a Contact (Priority: P1)

A sales rep creates a new contact record for an individual (name, email, phone, job title)
and links it to an existing or new company account. They can later search, filter, and update
the record.

**Why this priority**: Contacts are the foundational entity of the CRM; deals, support
tickets, and contracts all reference them.

**Independent Test**: Create a contact, link to a company, search for it by name, open the
record, and edit the phone number — confirm all changes persist.

**Acceptance Scenarios**:

1. **Given** a sales rep, **When** they create a contact with name and email, **Then** the
   record is saved and appears in the contact list immediately.
2. **Given** an existing contact, **When** a rep edits their job title, **Then** the change
   is saved with a timestamp and the editor's name in the activity log.
3. **Given** a duplicate email address, **When** a rep tries to create a new contact,
   **Then** the system warns about the potential duplicate and offers to view the existing
   record rather than silently creating a second one.

---

### User Story 2 - Manage Company Accounts (Priority: P1)

A user creates a company account (name, industry, size, website, address) and associates
multiple contacts to it. The account view shows all contacts, open deals, active contracts,
and support tickets in one place.

**Why this priority**: Account-level visibility is the primary context for enterprise sales
and support; all downstream modules roll up to accounts.

**Independent Test**: Create an account, link two contacts to it, open the account view, and
confirm both contacts, their deals, and open tickets appear in the timeline.

**Acceptance Scenarios**:

1. **Given** a user creating an account, **When** they save, **Then** the account appears in
   the account list and can be linked to contacts immediately.
2. **Given** an account with linked records, **When** a user views the account, **Then** they
   see a unified timeline of contacts, deals, contracts, and support tickets.
3. **Given** an account being merged with a duplicate, **When** the merge is confirmed,
   **Then** all linked records transfer to the surviving account and the duplicate is archived.

---

### User Story 3 - Lead Capture & Qualification (Priority: P2)

A Sales Rep creates a Lead record for an unqualified prospect. After
qualification, the lead is converted into a Contact + Account + Deal in one operation,
preserving all captured notes.

**Why this priority**: Separating unqualified leads from confirmed contacts keeps the contact
list clean and enables conversion-rate reporting.

**Independent Test**: Create a lead, add qualification notes, convert it, and confirm a
Contact, Account, and Deal are created with the lead's notes transferred.

**Acceptance Scenarios**:

1. **Given** a user, **When** they create a lead with name, email, and company name, **Then**
   the lead appears in the lead list with "New" status.
2. **Given** a qualified lead, **When** the user clicks Convert, **Then** the system creates
   a Contact, optionally a new Account, and optionally a new Deal in one step.
3. **Given** a lead marked as Disqualified, **When** the user provides a reason, **Then** the
   lead is archived with the reason and excluded from active pipeline counts.

---

### User Story 4 - Search, Filter & Segment Contacts (Priority: P2)

A user searches contacts by name, email, account, tag, or custom field. They save a filtered
view as a named segment (e.g., "Enterprise contacts in EMEA") for repeated use.

**Why this priority**: Large contact databases are only useful if reps can quickly find and
segment the right people for outreach and reporting.

**Independent Test**: Create 10 test contacts with varying attributes, apply a filter
combining account and tag, verify only matching contacts appear, then save as a segment.

**Acceptance Scenarios**:

1. **Given** a user on the contact list, **When** they type a name or email in the search
   bar, **Then** matching results appear within 1 second.
2. **Given** a filtered view, **When** the user saves it as a segment, **Then** it appears in
   the segment list and shows a live count of matching contacts.
3. **Given** a saved segment, **When** the underlying data changes, **Then** the segment
   count updates automatically on next load.

---

### Edge Cases

- What happens when a contact is linked to multiple accounts (e.g., a consultant)?
- How are duplicate contacts detected — exact email match only, or fuzzy name matching too?
- What happens to a contact's records when their linked account is deleted?
- Can contacts be imported in bulk via CSV, and how are conflicts resolved?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to create, read, update, and archive contacts with at minimum:
  name (required), email (required, valid format), phone, job title, linked account, and tags.
- **FR-002**: Users MUST be able to create, read, update, and archive company accounts with:
  name, industry, company size, website, billing address, and assigned owner.
- **FR-003**: System MUST detect potential duplicate contacts (same email) and prompt the user
  before saving.
- **FR-004**: Account detail view MUST aggregate all linked contacts, deals, contracts, and
  support tickets in a unified timeline.
- **FR-005**: Sales Reps MUST be able to create and manage Lead records distinct from
  confirmed contacts. Admins and Managers have read-only access to leads. Support Agents
  have no access to leads. Lead status MUST follow the lifecycle: New → Contacted →
  Qualified → Converted / Disqualified.
- **FR-006**: System MUST support Lead-to-Contact/Account/Deal conversion in a single
  operation, preserving all notes and activity history.
- **FR-007**: Users MUST be able to filter contacts by any field and save filters as named
  segments.
- **FR-008**: System MUST support bulk import of contacts via CSV with field mapping and
  two duplicate-resolution options selectable per import run: Skip (default — existing
  record is preserved) or Overwrite (existing record is updated with imported values).
- **FR-009**: All create, update, and archive actions MUST be recorded in a per-record
  activity log.
- **FR-011**: When a contact's linked account is archived, the contact MUST remain active.
  The archived account MUST be displayed with an "(archived)" indicator on the contact
  record and in all linked record views.
- **FR-010**: Contacts MUST support custom fields defined by Admins to capture domain-specific
  data.

### Key Entities

- **Contact**: Individual person with personal/professional details, linked to one or more
  accounts. Email is required and used as the primary deduplication key.
- **Account**: Company or organisation, parent entity for contacts, deals, and contracts.
- **Lead**: Unqualified prospect managed by Sales Reps. Status lifecycle: New → Contacted →
  Qualified → Converted / Disqualified. Converts to Contact + Account + Deal upon
  qualification.
- **Segment**: Named, saved filter expression applied to the contact or account list.
- **ActivityLog**: Per-record log of all changes, notes, emails, and linked events.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A sales rep can create a new contact and link it to an account in under 60
  seconds.
- **SC-002**: Contact search returns results in under 1 second for databases up to 100,000
  records.
- **SC-003**: Lead conversion (Lead → Contact + Account + Deal) completes in a single
  screen interaction in under 2 minutes.
- **SC-004**: Bulk CSV import of 1,000 contacts completes in under 2 minutes with a clear
  result summary (imported, skipped, errors).
- **SC-005**: Duplicate detection triggers on every save with zero false negatives for exact
  email matches.

## Assumptions

- A contact may be linked to multiple accounts (e.g., a consultant working across companies).
- Leads and Contacts are separate record types; a converted lead retains a link to the
  original lead record for audit purposes.
- Custom fields are defined globally by Admins and apply to all contacts/accounts.
- Archived records are retained for reporting and audit; they do not appear in active lists
  by default.
- Bulk import is limited to CSV format in v1; API-based import is out of scope for this
  module.
- Contact email is required and serves as the primary deduplication key; two contacts
  cannot share the same email address.
- When a contact's linked account is archived, the contact remains active and retains the
  reference; archiving an account does not cascade to its contacts.
- Lead status follows a defined lifecycle: New → Contacted → Qualified → Converted /
  Disqualified. Only Sales Reps may create or update leads; Admins and Managers have
  read-only access; Support Agents have no access.
- CSV bulk import offers two duplicate-resolution modes per run: Skip (default) or
  Overwrite. "Create anyway" is not supported — duplicate contacts are never silently
  created via import.
