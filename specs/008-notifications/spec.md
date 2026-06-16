# Feature Specification: Notifications & Alerts

**Feature Branch**: `008-notifications`

**Created**: 2026-06-15

**Status**: Draft

**Input**: User description: "CRM application — Notifications & Alerts module (in-app web notifications only). Email and push notifications are out of scope for v1."

## Clarifications

### Session 2026-06-15

- Q: Which notification channels are in scope for v1? → A: In-app (web) only. Email and push notifications are out of scope for v1.

### Session 2026-06-16

- Q: What mechanism delivers real-time notifications to active sessions? → A: Server-Sent Events (SSE) — one-way server push over HTTP; client reconnects automatically.
- Q: Can Admin notification rules use free-form trigger conditions? → A: No — rules are limited to FR-001 event types with one optional filter per rule (e.g., deal value >, priority =).
- Q: How many notifications load in the panel, and is there pagination? → A: Load 20 most recent; infinite scroll fetches more on demand.
- Q: Does the 90-day retention apply to unread notifications too? → A: Retention reduced to 30 days for all notifications — read and unread alike.
- Q: Are "comment" and "mention" one toggle or separate? → A: Separate — Comments and Mentions are independently configurable event types.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - In-App Notifications (Priority: P1)

A user sees a notification bell in the top navigation. When a deal is assigned to them, a
support ticket is updated, or a contract is due for renewal, a badge appears and clicking
the bell shows a list of recent notifications with links to the relevant records.

**Why this priority**: In-app notifications are the sole real-time awareness mechanism for
users actively working in the CRM web application.

**Independent Test**: Assign a deal to a test user, log in as that user, and confirm the
notification bell shows a badge and the notification links to the correct deal.

**Acceptance Scenarios**:

1. **Given** a deal assigned to a user, **When** the user is logged in, **Then** a
   notification badge appears on the bell within 5 seconds.
2. **Given** unread notifications, **When** the user opens the notification panel, **Then**
   they see a list sorted by most recent, each with a title, timestamp, and link to the
   source record.
3. **Given** a user clicking "Mark all as read", **When** confirmed, **Then** the badge
   clears and all notifications are marked read.

---

### User Story 2 - Notification Preferences (Priority: P2)

A user opens Notification Settings and toggles which event types (assignment, comment/mention,
status change, contract renewal due, deal stage change) generate in-app notifications.

**Why this priority**: Users with high activity volumes need to suppress low-signal events to
stay focused; users with low activity need all events on.

**Independent Test**: Disable in-app notifications for "comment" events, trigger a comment on
a watched record, and confirm no notification badge appears.

**Acceptance Scenarios**:

1. **Given** a user on the Notification Settings page, **When** they toggle off "Comments",
   **Then** subsequent comments on their records generate no notification.
2. **Given** a user enabling "Contract Renewal Reminders", **When** a contract enters the
   30-day renewal window, **Then** an in-app notification is delivered on their next login.
3. **Given** a user saving preferences, **When** they reload the page, **Then** their saved
   preferences are reflected correctly.

---

### User Story 3 - Admin Notification Rules (Priority: P2)

An Admin configures organisation-wide in-app notification rules (e.g., "notify Admins
when a high-value deal is created"). These rules fire regardless of individual preferences.

**Why this priority**: Critical business events must reach the right people even if individuals
have suppressed that event type in their personal preferences.

**Independent Test**: Create an Admin rule for deal value above a threshold, create such a
deal, and confirm the designated recipient sees the notification in their bell panel.

**Acceptance Scenarios**:

1. **Given** an Admin rule targeting a role, **When** the trigger event occurs, **Then** all
   users with that role receive an in-app notification regardless of personal preferences.
2. **Given** an Admin rule, **When** an Admin disables it, **Then** no further notifications
   fire for that rule without affecting personal preferences.

---

### Edge Cases

- How are notification storms prevented when a bulk action triggers hundreds of assignments?
- What is the retention period for read notifications?
- Can users disable Admin-rule notifications?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST deliver in-app notifications for the following event types: record
  assignment, comment, mention, status change, contract renewal due, deal stage change, and
  SLA breach. Comments and Mentions are distinct event types with independent toggles.
- **FR-002**: In-app notifications MUST appear in the UI within 5 seconds of the triggering
  event for users with active sessions, delivered via Server-Sent Events (SSE). Users who
  are logged out accumulate notifications server-side and see all pending notifications on
  their next login.
- **FR-003**: Users MUST be able to toggle in-app notifications per event type from their
  Notification Settings page. Comments and Mentions MUST be separately toggleable.
- **FR-004**: Admins MUST be able to create organisation-wide notification rules that fire
  regardless of individual preferences; users cannot suppress Admin-rule notifications.
  Rules MUST be limited to the event types defined in FR-001, with one optional filter
  condition per rule (e.g., deal value >, priority =, status =). Free-form rule expressions
  are out of scope for v1.
- **FR-005**: System MUST batch notifications when a single action triggers more than 10
  notifications for the same user (e.g., bulk assignment), delivering a single digest entry
  instead of individual items.
- **FR-006**: All notifications MUST be purged automatically after 30 days, regardless of
  read status. No manual action is required; the purge job runs on a scheduled basis.
- **FR-007**: Email notifications are explicitly out of scope for v1.
- **FR-008**: Push notifications (mobile) are explicitly out of scope for v1.
- **FR-009**: The notification panel MUST load the 20 most recent notifications on open;
  additional notifications MUST be fetchable via infinite scroll.

### Key Entities

- **Notification**: A record of an event targeting a user, with status (unread/read),
  timestamp, event type, and link to the source record.
- **NotificationPreference**: Per-user, per-event-type toggle (in-app only). Comments and
  Mentions are stored as separate preference entries.
- **AdminNotificationRule**: Organisation-wide rule defining trigger event (from FR-001
  event types), one optional filter condition (e.g., deal value >, priority =), and target
  audience (role or specific user).
- **NotificationDigest**: Batched notification combining more than 10 same-type events into
  one panel entry.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In-app notification badge appears within 5 seconds of a triggering event for
  active sessions.
- **SC-002**: Pending notifications accumulated while a user was logged out are all visible
  within 2 seconds of their next login.
- **SC-003**: Users can configure all notification preferences in under 2 minutes.
- **SC-004**: Bulk actions triggering > 10 notifications for one user result in a single
  digest entry — zero individual notification flood.
- **SC-005**: All notifications older than 30 days are purged automatically without any
  manual action, regardless of read status.

## Assumptions

- Only the in-app (web) notification channel is supported in v1; email and push are deferred.
- Users who are logged out accumulate notifications server-side; they see all pending
  notifications on next login.
- Users cannot suppress Admin-rule notifications regardless of personal preferences.
- Notification preferences are per-user; team-level preferences are not supported in v1.
- The 30-day retention policy applies to all notifications regardless of read status;
  unread notifications are not given special retention treatment.
- Real-time delivery to active sessions is implemented via Server-Sent Events (SSE);
  the client reconnects automatically on disconnect.
- Admin notification rules are constrained to FR-001 event types with one optional filter
  condition per rule; free-form rule expressions are out of scope for v1.
- The notification panel loads 20 most recent items on open; further items are fetched via
  infinite scroll.
- Comments and Mentions are separate event types with independent user preference toggles.
