# Feature Specification: Authentication

**Feature Branch**: `005-authentication`

**Created**: 2026-06-15

**Status**: Draft

**Input**: User description: "CRM application — Authentication module (username/password login, local user storage). MFA, SSO, and RBAC are out of scope."

## Clarifications

### Session 2026-06-16

- Q: Does the Auth module store the user's role, or is that deferred to Module 6? → A: Auth stores `role` on the User entity; Module 6 manages role assignment UI.
- Q: What happens UX-wise when a session expires during active use? → A: Hard redirect to the login page — unsaved work is lost; simpler v1 behaviour acceptable.
- Q: Is "locked" (after failed attempts) a separate state from "inactive"? → A: Yes — `locked` is a separate boolean flag independent of `active/inactive` status.
- Q: Which password hashing algorithm should be used? → A: bcrypt with a cost factor of ≥ 12.
- Q: What format must usernames follow? → A: Email address — valid email format, case-insensitive unique.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register a New User (Priority: P1)

An administrator creates a new user account by entering a username and password. The new
user can immediately log in with those credentials.

**Why this priority**: User accounts must exist before anyone can access the CRM.

**Independent Test**: Create a new user via the admin panel, log in with those credentials,
and confirm the dashboard loads.

**Acceptance Scenarios**:

1. **Given** an admin, **When** they submit a new username and password, **Then** the account
   is created and appears in the user list.
2. **Given** a username that already exists, **When** the admin tries to create it again,
   **Then** an error message indicates the username is taken.
3. **Given** a password shorter than 8 characters, **When** submitted, **Then** an inline
   validation error blocks the form submission.

---

### User Story 2 - Log In (Priority: P1)

A user navigates to the login page, enters their username and password, and lands on the
CRM dashboard.

**Why this priority**: This is the entry point to the entire application.

**Independent Test**: Enter valid credentials on the login page and confirm redirect to the
dashboard. Enter invalid credentials and confirm an error is shown.

**Acceptance Scenarios**:

1. **Given** valid credentials, **When** the user submits the login form, **Then** they are
   redirected to the dashboard and a session is established.
2. **Given** an incorrect password, **When** submitted, **Then** a generic error "Invalid
   username or password" is shown (no account enumeration).
3. **Given** 5 consecutive failed attempts, **When** the user tries again, **Then** the
   account is temporarily locked and a message instructs them to contact an admin.

---

### User Story 3 - Log Out (Priority: P1)

A logged-in user clicks the logout button and is redirected to the login page. Their session
is invalidated so the browser back button cannot return them to a protected page.

**Why this priority**: Session termination is a basic security and UX requirement.

**Independent Test**: Log in, click logout, then press the browser back button — confirm the
login page is shown, not the dashboard.

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they click Logout, **Then** their session is
   invalidated and they are redirected to the login page.
2. **Given** an invalidated session, **When** the user navigates to a protected URL,
   **Then** they are redirected to the login page.

---

### User Story 4 - Admin Resets a User's Password (Priority: P2)

An admin sets a new password for a user (e.g., when the user forgets theirs). The user can
then log in with the new password.

**Why this priority**: No self-service password reset is in scope; admin-mediated reset is the
only recovery path.

**Independent Test**: Reset a test user's password as admin, log in with the new password,
confirm access, and confirm the old password no longer works.

**Acceptance Scenarios**:

1. **Given** an admin, **When** they set a new password for a user, **Then** the change is
   saved and the old password is invalidated immediately.
2. **Given** the affected user's active session, **When** the password is reset by admin,
   **Then** that session is invalidated and the user must log in again.

---

### Edge Cases

- What happens when the session expires while the user is actively using the app?
- What happens if two admins reset the same user's password simultaneously?
- Can an admin deactivate an account without deleting it?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow admins to create user accounts with an email address (used
  as username), password, and an assigned role (Admin, Manager, Sales Rep, or Support Agent).
  Role assignment is required at creation; it may be changed later via Module 6.
- **FR-002**: Passwords MUST be stored using bcrypt with a cost factor of ≥ 12; plaintext
  storage is forbidden.
- **FR-003**: Usernames MUST be valid email addresses. Email addresses MUST be unique
  across the system (case-insensitive comparison); the system MUST normalise emails to
  lowercase on storage.
- **FR-004**: Passwords MUST be at least 8 characters long; no other complexity rules are
  enforced in v1.
- **FR-005**: System MUST authenticate users with username and password on the login form.
- **FR-006**: System MUST return a generic error message for any failed login attempt (no
  indication of whether the username or password was wrong).
- **FR-007**: System MUST set a `locked` boolean flag on the User record after 5 consecutive
  failed login attempts. The `locked` flag is independent of the `active/inactive` status —
  a locked account may still be active. Only an admin can clear the `locked` flag to restore
  login access.
- **FR-008**: Sessions MUST expire after 30 minutes of inactivity. When a session expires,
  the user MUST be hard-redirected to the login page; any unsaved in-progress work is lost.
  No session-expiry modal or activity-based renewal is provided in v1.
- **FR-009**: Logout MUST immediately invalidate the session server-side.
- **FR-010**: Admins MUST be able to reset any user's password; the reset MUST invalidate all
  existing sessions for that user.
- **FR-011**: Admins MUST be able to deactivate a user account, preventing login without
  deleting the account or its associated records.

### Key Entities

- **User**: Account record with email address (username, lowercase-normalised), bcrypt-hashed
  password, role (Admin | Manager | Sales Rep | Support Agent), `active` boolean, and
  `locked` boolean. `active` and `locked` are independent flags.
- **Session**: Time-bound authenticated context linked to a user; expires on inactivity or
  logout.
- **FailedLoginAttempt**: Counter per username used to trigger lockout after 5 failures.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Login form submission and dashboard redirect completes in under 2 seconds.
- **SC-002**: Account lockout triggers exactly on the 5th failed attempt with no false
  positives for valid credentials.
- **SC-003**: Session expiry redirects to the login page within 1 second of the inactivity
  timeout.
- **SC-004**: Admin can create a new user account in under 1 minute.
- **SC-005**: Password reset by admin takes effect immediately — old password fails on the
  very next attempt.

## Assumptions

- User data is stored locally in SQLite; no external identity provider or directory service
  is used.
- There is no self-service registration; all accounts are created by an admin.
- There is no self-service "Forgot Password" flow; users must ask an admin to reset their
  password.
- MFA, SSO, and role-based access control are explicitly out of scope for this module.
- A single admin account is seeded at system setup time; subsequent admins are created by
  that account.
- Users are assigned one of four roles at account creation: Admin, Manager, Sales Rep, or
  Support Agent. Role determines data scope and feature access across all CRM modules.
  Role assignment UI is managed by Module 6 (User & Team Management).
- Session tokens are stored server-side; the client holds only an opaque session identifier.
- Usernames are email addresses; they are normalised to lowercase on storage and compared
  case-insensitively for uniqueness.
- Passwords are hashed with bcrypt at cost factor ≥ 12; no other algorithm is permitted.
- `locked` (security lockout) and `active/inactive` (admin-controlled) are separate boolean
  flags on the User record; an admin may clear either independently.
- On session expiry, users are hard-redirected to the login page; unsaved work is lost.
  This is an accepted v1 limitation.
