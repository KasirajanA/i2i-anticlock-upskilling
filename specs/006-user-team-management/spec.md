# Feature Specification: User & Team Management

**Feature Branch**: `006-user-team-management`

**Created**: 2026-06-15

**Status**: Draft

**Input**: User description: "CRM application — User & Team Management module (user profiles, teams, minimal role management for CRM access control)."

## Clarifications

### Session 2026-06-16

- Q: What is Manager's module access scope? → A: Org-wide read on all modules except User & Team Mgmt; no write or admin capabilities.
- Q: Can user accounts be hard-deleted? → A: No — deactivation is the only removal mechanism; hard delete removed from FR-004.
- Q: What access does a user retain after their role changes? → A: Existing assignments remain visible; role change only restricts new access going forward.
- Q: Are Auth and User Mgmt User records the same DB record or separate? → A: One User table — Auth and User Mgmt operate on the same record; profile fields extend it.
- Q: Can users change their own password from the profile page? → A: Yes — requires current password confirmation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create & Manage Users (Priority: P1)

An admin creates a new CRM user, assigns them a role (Admin, Sales Rep, or Support Agent),
and the user can immediately log in and access the modules their role permits.

**Why this priority**: Users cannot work in the CRM until they have an account with the
correct role; role determines which navigation items and modules are visible.

**Independent Test**: Create a Support Agent user, log in as that user, and confirm the
Sales Pipeline module is not visible or accessible.

**Acceptance Scenarios**:

1. **Given** an admin, **When** they create a user and assign the Sales Rep role, **Then**
   the user can access Contacts, Sales Pipeline, and Contract Management but not the Support
   queue.
2. **Given** an admin changing a user's role from Sales Rep to Support Agent, **When** saved,
   **Then** the change takes effect on the user's next page load without requiring logout.
3. **Given** an admin deactivating a user, **When** confirmed, **Then** the user cannot log
   in and their open records remain accessible to other team members.

---

### User Story 2 - Manage Own Profile (Priority: P2)

A logged-in user updates their display name, avatar, and time zone from their profile
settings page.

**Why this priority**: Display name appears throughout the CRM; time zone affects how all
dates and times are rendered for that user.

**Independent Test**: Update display name and time zone on a test account; confirm the new
name appears in the top navigation and that a deal's close date renders in the updated time
zone.

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they update their display name and save, **Then** the
   new name appears everywhere in the UI immediately.
2. **Given** a user changing their time zone, **When** saved, **Then** all date/time fields
   in the CRM render in the selected time zone.
3. **Given** a user uploading an avatar larger than 2 MB or a non-image file, **When**
   submitted, **Then** an inline error prevents the upload.

---

### User Story 3 - Create & Manage Teams (Priority: P2)

An Admin creates a named team (e.g., "EMEA Sales"), assigns existing users as
members, and optionally designates a team lead. Records such as deals and support tickets
can then be assigned to a team.

**Why this priority**: Teams are the primary way to segment pipelines, support queues, and
reports across the CRM.

**Independent Test**: Create a team, add two members, assign a deal to the team, and confirm
both members can view the deal while a user outside the team cannot.

**Acceptance Scenarios**:

1. **Given** a manager, **When** they create a team and add members, **Then** the team name
   appears in all assignment dropdowns across the CRM.
2. **Given** a team with a designated lead, **When** a new record is assigned to the team
   without a specific owner, **Then** the system suggests the team lead as the default
   assignee.
3. **Given** a user removed from a team, **When** the change is saved, **Then** they no
   longer appear in that team's assignment dropdown.

---

### Edge Cases

- What happens when the last Admin user is deactivated?
- Can a user belong to more than one team?
- What access does a user retain after their role changes — do existing record assignments
  still show in their view?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support exactly four roles: **Admin**, **Manager**, **Sales Rep**,
  and **Support Agent**. Role assignment is done by an Admin at account creation or any time
  after.
- **FR-002**: Role-based module visibility MUST follow this matrix:

  | Module               | Admin | Manager       | Sales Rep | Support Agent |
  |----------------------|-------|---------------|-----------|---------------|
  | User & Team Mgmt     | ✅    | ❌            | ❌        | ❌            |
  | Contact Management   | ✅    | ✅ (read)     | ✅        | ✅ (read)     |
  | Sales Pipeline       | ✅    | ✅ (read)     | ✅        | ❌            |
  | Contract Management  | ✅    | ✅ (read)     | ✅        | ❌            |
  | Customer Support     | ✅    | ✅ (read)     | ❌        | ✅            |
  | Analytics & Reporting| ✅    | ✅ (all data) | ✅ (own)  | ✅ (own)      |

  Manager has org-wide read access to all modules except User & Team Mgmt; Managers have
  no write or admin capabilities in any module.

- **FR-003**: Users with no access to a module MUST NOT see it in the navigation; direct URL
  access MUST redirect to an "Access Denied" page.
- **FR-004**: Admins MUST be able to create, edit, and deactivate user accounts. Hard
  deletion of user accounts is not permitted; deactivation is the only removal mechanism.
- **FR-005**: Admins MUST be able to change a user's role at any time; the change MUST take
  effect on the user's next page load. Existing record assignments remain visible to the
  user after a role change; only new access is restricted by the new role.
- **FR-006**: Users MUST be able to update their display name, avatar, time zone, and
  password from their profile page. A password change MUST require the user to enter their
  current password before setting a new one.
- **FR-007**: Admins MUST be able to create named teams and add or remove members.
  Managers have no access to User & Team Management and cannot create or modify teams.
- **FR-008**: Each team MAY have one designated team lead; the lead is used as the default
  assignee for unowned team records.
- **FR-009**: System MUST prevent deactivation of the last active Admin account.
- **FR-010**: A user MAY belong to multiple teams simultaneously.

### Key Entities

- **User**: Single shared DB record used by both Auth and User Mgmt. Auth fields: email
  (username), bcrypt-hashed password, `active` boolean, `locked` boolean. User Mgmt fields:
  display name, avatar, time zone. Shared field: role (Admin | Manager | Sales Rep |
  Support Agent).
- **Role**: One of four fixed values — Admin, Manager, Sales Rep, Support Agent. Not
  extensible in v1.
- **Team**: Named group of users with an optional designated lead; used for record assignment
  and reporting segmentation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An admin can create a new user, assign a role, and have that user ready to log
  in within 1 minute.
- **SC-002**: Role change takes effect within one page reload — no logout or cache clear
  required.
- **SC-003**: A user with an incorrect role receives an "Access Denied" response for every
  restricted module — zero bypass paths exist, validated by manual role-matrix testing before
  launch.
- **SC-004**: Team creation with up to 20 members completes in under 30 seconds.
- **SC-005**: Deactivating a user account takes effect immediately — the user's active session
  is terminated within 5 seconds of admin confirmation.

## Assumptions

- Roles are fixed (Admin, Manager, Sales Rep, Support Agent); custom roles are out of scope
  for v1.
- Permissions are coarse-grained at the module level; action-level permissions (e.g.,
  read vs. edit within a module) are not enforced in v1.
- The Support Agent role has read-only access to Contacts (to look up customer details) but
  cannot create or edit contacts.
- Sales Reps and Support Agents see only Analytics data scoped to their own records; Managers
  and Admins see full organisation-wide data.
- User accounts are created by Admins only; there is no self-registration.
- A user may belong to multiple teams; their effective access is the union of their role
  permissions (role drives module access, not team membership).
- The first Admin account is seeded at system setup; it cannot be deactivated unless another
  Admin exists.
- User accounts cannot be hard-deleted; deactivation is the only removal mechanism to
  preserve referential integrity across deals, tickets, contracts, and reports.
- Role changes are forward-only: existing record assignments remain visible to the user;
  only new module access is restricted by the updated role.
- Auth and User Mgmt operate on a single shared User table; there is no separate credential
  record. Profile fields (display name, avatar, time zone) extend the Auth User entity.
- Users may change their own password from the profile page by confirming their current
  password; this is distinct from admin-reset (which requires no current password).
