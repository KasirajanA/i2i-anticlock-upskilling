# Feature Specification: Customer Support

**Feature Branch**: `003-customer-support`

**Created**: 2026-06-15

**Status**: Draft

**Input**: User description: "CRM application — Customer Support module (support tickets, lifecycle management, assignment, SLA tracking)."

## Clarifications

### Session 2026-06-15

- Q: Is "team lead" a separate formal role or an Admin user? → A: Admin — no separate role; Admins receive SLA breach and orphaned-ticket alerts.
- Q: What format should ticket IDs follow? → A: Auto-generated prefixed sequential — e.g., I2I-CRM-0001, I2I-CRM-0002.
- Q: What happens if a ticket's linked contact is deleted? → A: Allow deletion; ticket retains contact name as a read-only snapshot for audit.
- Q: When a Resolved ticket is re-opened by a customer reply, does the SLA clock reset? → A: No — original SLA record is preserved; a new SLA record is created for the re-opened ticket.
- Q: Via which channel are SLA breach and re-open notifications delivered? → A: In-app notification only (consistent with Module 1); email is out of scope for v1.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a Support Ticket (Priority: P1)

A Support Agent or Admin creates a new support ticket on behalf of a customer, linking it
to an existing contact and account, setting a priority, and describing the issue.

**Why this priority**: Ticket creation is the entry point to every customer support
interaction; all other stories depend on a ticket existing.

**Independent Test**: Create a ticket linked to a test contact with "High" priority, confirm
it appears in the ticket queue with status "Open" and the correct priority badge.

**Acceptance Scenarios**:

1. **Given** a Support Agent, **When** they submit a new ticket with contact, subject, and
   priority, **Then** the ticket is saved with status "Open" and a unique ticket ID assigned.
2. **Given** a missing required field (contact or subject), **When** submitted, **Then**
   inline validation blocks the form.
3. **Given** a created ticket, **When** the linked contact views their account page,
   **Then** the new ticket appears in the account's support history.

---

### User Story 2 - Manage Ticket Lifecycle (Priority: P1)

A Support Agent picks up an Open ticket, moves it to In Progress, adds internal notes and
customer-facing replies, and eventually resolves and closes it.

**Why this priority**: The ticket lifecycle is the core workflow for every support agent;
it must be clear and fast to operate.

**Independent Test**: Open a ticket, change status to In Progress, add a reply, mark it
Resolved, then Closed — confirm each transition is logged and the SLA timer records the
resolution time.

**Acceptance Scenarios**:

1. **Given** an Open ticket, **When** an agent changes it to In Progress, **Then** the
   status updates and the change is logged with timestamp and agent name.
2. **Given** an In Progress ticket, **When** the agent marks it Resolved, **Then** the SLA
   resolution time is recorded and the linked contact is notified.
3. **Given** a Resolved ticket, **When** marked Closed, **Then** it moves to the closed
   queue and no further status changes are permitted (except by Admins).
4. **Given** a customer reply on a Resolved ticket, **When** received, **Then** the ticket
   is automatically re-opened and the assigned agent is notified.

---

### User Story 3 - Ticket Assignment & Queue Management (Priority: P1)

An Admin assigns open tickets to specific agents or to a support team. Agents
see only their assigned tickets by default; unassigned tickets appear in a shared queue.

**Why this priority**: Without clear ownership, tickets get missed; the queue view ensures
no ticket falls through the cracks.

**Independent Test**: Create two tickets — assign one to a test agent and leave one
unassigned. Log in as the agent and confirm only their assigned ticket appears in "My
Tickets" while the unassigned one is in the "Unassigned" queue.

**Acceptance Scenarios**:

1. **Given** an unassigned ticket, **When** an Admin assigns it to an agent, **Then** it
   moves from the shared queue to the agent's personal queue and the agent is notified.
2. **Given** an agent's queue, **When** they self-assign an unassigned ticket, **Then** it
   immediately appears in their personal queue.
3. **Given** a ticket assigned to an inactive user, **When** an Admin views the queue,
   **Then** the ticket appears in an "Orphaned" state with a prompt to reassign.

---

### User Story 4 - SLA Tracking (Priority: P2)

Each ticket has a target first-response time and resolution time based on priority.
Tickets breaching their SLA are visually flagged and the team lead is notified.

**Why this priority**: SLA adherence is the primary metric for support quality; breaches
must be visible before they happen.

**Independent Test**: Create a High-priority ticket, let the first-response SLA window pass
without a reply, and confirm the ticket is flagged as "SLA Breached" and the team lead
receives a notification.

**Acceptance Scenarios**:

1. **Given** a new High-priority ticket, **When** the first-response window (4 hours) passes
   without a reply, **Then** the ticket is flagged "SLA Breached" and the team lead is
   notified.
2. **Given** a ticket approaching its resolution SLA (< 1 hour remaining), **When** still
   open, **Then** it is visually highlighted as "SLA Warning" in the queue.
3. **Given** an agent adding a reply within the SLA window, **When** saved, **Then** the
   first-response SLA is marked met and the warning indicator clears.

---

### Edge Cases

- What happens to open tickets when a support agent is deactivated?
- Can a ticket be linked to multiple contacts (e.g., CC'd stakeholders)?
- How are duplicate tickets for the same issue detected and merged?
- What happens if a ticket's linked contact is deleted?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to create tickets with: linked contact (required), linked
  account (auto-filled from contact), subject (required), description, priority, and
  assigned agent (optional at creation). Each ticket MUST be assigned an auto-generated
  reference ID in the format `I2I-CRM-NNNN` (e.g., I2I-CRM-0001) on creation.
- **FR-002**: Ticket priority MUST support four levels: Low, Medium, High, Critical.
- **FR-003**: Tickets MUST follow this lifecycle: Open → In Progress → Resolved → Closed.
  Admins may revert any status; agents may only advance forward.
- **FR-004**: All status transitions, assignments, and replies MUST be logged in the ticket's
  activity log with timestamp and acting user.
- **FR-005**: SLA targets MUST be defined per priority level:
  - Critical: first response 1 h, resolution 4 h
  - High: first response 4 h, resolution 24 h
  - Medium: first response 8 h, resolution 48 h
  - Low: first response 24 h, resolution 72 h
- **FR-006**: Tickets breaching first-response or resolution SLA MUST be flagged visually
  in the queue and trigger an in-app notification to an Admin. Email notifications are
  out of scope for v1.
- **FR-007**: A customer reply on a Resolved ticket MUST automatically re-open the ticket,
  create a new SLA record for the re-opened cycle (the original SLA record is preserved),
  and deliver an in-app notification to the assigned agent.
- **FR-008**: Agents MUST be able to add internal notes (visible to agents only) and
  customer-facing replies on any ticket.
- **FR-009**: Unassigned tickets MUST appear in a shared queue visible to all Support Agents
  and Admins.
- **FR-010**: Ticket list MUST be filterable by status, priority, assigned agent, account,
  and date range.
- **FR-011**: When a linked contact is deleted, the ticket MUST retain a read-only snapshot
  of the contact's name and original ID for audit purposes; contact deletion MUST NOT be
  blocked by existing tickets.

### Key Entities

- **Ticket**: Core record with auto-generated reference ID (`I2I-CRM-NNNN`), subject,
  description, status, priority, linked contact (with read-only name snapshot retained
  on contact deletion), linked account, and assigned agent.
- **TicketStatus**: Open, In Progress, Resolved, Closed.
- **TicketPriority**: Low, Medium, High, Critical.
- **Reply**: Customer-facing message or internal note added to a ticket thread.
- **SLARecord**: Timestamps for first response, resolution target, actual first response,
  and actual resolution — used for SLA breach detection and reporting. Multiple SLARecords
  may exist per ticket; each re-open cycle creates a new record while preserving prior ones.
- **ActivityLog**: Per-ticket log of status changes, assignments, edits, and system events.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A Support Agent can create and submit a new ticket in under 60 seconds.
- **SC-002**: SLA breach flag appears within 5 minutes of the SLA deadline passing — no
  manual refresh required.
- **SC-003**: Ticket queue loads within 2 seconds for queues of up to 1,000 open tickets.
- **SC-004**: Auto-reopen on customer reply occurs within 1 minute of the reply being
  recorded.
- **SC-005**: Zero tickets with deactivated agents remain in an unnotified orphaned state —
  an Admin is alerted via in-app notification within 5 minutes of agent deactivation.

## Assumptions

- Customer replies are entered manually by agents in v1; email-to-ticket ingestion is out
  of scope.
- SLA targets are fixed by priority level and configured at system setup; per-account
  custom SLAs are out of scope for v1.
- A ticket is linked to exactly one contact; CC/multi-contact is out of scope for v1.
- Ticket merging is out of scope for v1; agents should close the duplicate manually.
- Support Agents can view linked contact and account details (read-only) to provide context
  for their replies.
- Business hours are not factored into SLA calculations in v1; SLA timers run 24/7.
- "Team Lead" is not a separate system role; Admin users perform all team lead
  responsibilities including SLA breach alerts, orphaned ticket alerts, and queue management.
- Ticket IDs are auto-generated in the format `I2I-CRM-NNNN` (e.g., I2I-CRM-0001) on creation.
- If a contact is deleted, their tickets retain a read-only name snapshot; deletion is not
  blocked by existing ticket references.
- When a Resolved ticket is re-opened by a customer reply, the original SLA record is
  preserved and a new SLA record is created for the re-opened cycle.
- All system notifications (SLA breach, ticket assignment, agent re-open alert) are delivered
  via in-app notification only; email notifications are out of scope for v1.
