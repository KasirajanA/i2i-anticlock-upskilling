# Quickstart Validation Guide: Authentication (Module 005)

**Prerequisites**: Backend running on `http://localhost:8000`, frontend on `http://localhost:5173`. SQLite DB initialised (`alembic upgrade head`). Seed script run to create initial Admin.

---

## Setup

```bash
# Backend
cd backend
export SEED_ADMIN_EMAIL=admin@example.com
export SEED_ADMIN_PASSWORD=admin1234
python -m app.core.seed   # creates initial Admin if none exists
python -m uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev

# Run backend tests
cd backend && pytest tests/auth/ -v

# Run frontend tests
cd frontend && npm test -- --testPathPattern=auth
```

---

## Scenario 1 — Successful Login and Redirect (FR-005, SC-001)

1. Navigate to `http://localhost:5173/login`.
2. Enter `admin@example.com` / `admin1234`. Submit.

**Expected**:
- Redirect to `/dashboard` in ≤ 2 s.
- `crm_session` cookie is set (`HttpOnly`, `SameSite=Strict`).
- `GET /api/v1/auth/me` returns `{"role": "admin", "active": true, "locked": false}`.

---

## Scenario 2 — Invalid Credentials (FR-006)

1. On the login page, enter `admin@example.com` / `wrongpassword`. Submit.

**Expected**:
- Generic error message: `"Invalid username or password"` — no indication of which field is wrong.
- HTTP 401 returned from `POST /api/v1/auth/login`.
- Cookie is **not** set.

---

## Scenario 3 — Account Lockout After 5 Failures (FR-007, SC-002)

1. Submit the login form with a wrong password 5 times for the same email.

**Expected**:
- On the 5th failure, the response includes `"Your account has been locked. Please contact an administrator."`.
- 6th attempt with the *correct* password also returns 401 (account is locked).
- `users.locked = true` in the DB.

**Unlock**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/users/1/unlock \
  -H "Cookie: crm_session=<admin_session>"
```

---

## Scenario 4 — Session Expiry (FR-008, SC-003)

> Use the test endpoint to fast-forward session `last_active_at`.

1. Log in. Note the `crm_session` cookie value.
2. `POST /api/v1/_test/sessions/expire?session_id=<sid>` (sets `last_active_at` to 31 minutes ago).
3. Navigate to any protected page.

**Expected**:
- Hard redirect to `/login` within 1 s.
- No modal or warning — just immediate redirect.
- Back button from `/login` does not return to the dashboard.

---

## Scenario 5 — Logout (FR-009)

1. Log in. Navigate to the dashboard.
2. Click **Logout**.

**Expected**:
- Redirect to `/login`.
- `crm_session` cookie is cleared (`Max-Age=0`).
- Pressing browser back button shows the login page (session is server-side invalidated).
- Direct `GET /api/v1/auth/me` with old cookie returns HTTP 401.

---

## Scenario 6 — Admin Creates a New User (FR-001, SC-004)

1. Log in as Admin.
2. Submit: `POST /api/v1/auth/users` with `{"email": "newrep@example.com", "password": "password1", "role": "sales_rep", "display_name": "New Rep"}`.

**Expected**:
- HTTP 201 with new user object.
- New user can log in immediately with the provided credentials.

**Inline validation**:
- Submit with `password: "short"` → HTTP 422 `"password must be at least 8 characters"`.
- Submit with duplicate email → HTTP 409.

---

## Scenario 7 — Admin Resets Password (FR-010, SC-005)

1. Log in as Admin and as User A in separate browser profiles.
2. Admin: `POST /api/v1/auth/users/{user_a_id}/reset-password` with new password.

**Expected**:
- HTTP 204.
- User A's existing session is immediately invalidated — their next request returns 401.
- User A can log in with the new password.
- Old password returns 401.

---

## Scenario 8 — Deactivate User (FR-011)

1. Admin: `POST /api/v1/auth/users/{user_id}/deactivate`.

**Expected**:
- HTTP 204.
- Deactivated user's session is terminated.
- Login attempt with deactivated account returns 401 (same generic message).

**Last Admin guard**:
- Attempt to deactivate the only active Admin → HTTP 409.

---

## Unit Test Checklist

| Test File | Coverage |
|-----------|----------|
| `tests/unit/test_auth_service.py` | Login flow, lockout counter, dummy bcrypt run, session creation |
| `tests/unit/test_password_hasher.py` | bcrypt hash/verify, cost factor |
| `tests/unit/test_session_middleware.py` | Expiry check, `last_active_at` update, 401 on expiry |
| `tests/integration/test_login_api.py` | Success, invalid creds, locked, inactive — all return same 401 |
| `tests/integration/test_admin_users_api.py` | Create, reset password, deactivate, unlock, last-admin guard |
| `frontend/tests/LoginPage.test.tsx` | Form validation, error display, redirect on success |
| `frontend/tests/SessionGuard.test.tsx` | 401 → redirect, session expiry handling |
