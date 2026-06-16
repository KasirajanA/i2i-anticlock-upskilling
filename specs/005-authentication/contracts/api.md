# API Contract: Authentication (Module 005)

**Base path**: `/api/v1/auth`  
**Session cookie**: `crm_session` — `HttpOnly; Secure; SameSite=Strict`  
**Content-Type**: `application/json`

---

## Login

### `POST /api/v1/auth/login`

Authenticate with email and password.

**Request body**
```json
{
  "email": "alice@example.com",
  "password": "s3cur3pass"
}
```

**Response 200** — Sets `crm_session` cookie
```json
{
  "user": {
    "id": 1,
    "email": "alice@example.com",
    "role": "admin",
    "display_name": "Alice Smith",
    "active": true
  }
}
```

**Response 401** (invalid credentials, locked account, or inactive account — all return same body)
```json
{
  "type": "https://crm.i2i.io/errors/authentication-failed",
  "title": "Authentication Failed",
  "status": 401,
  "detail": "Invalid username or password."
}
```

**Note**: Identical response body and approximate response time for any failure (bcrypt dummy run prevents timing enumeration).

---

## Logout

### `POST /api/v1/auth/logout`

Invalidate the current session server-side.

**Auth**: Requires valid `crm_session` cookie.

**Response 204** — Clears `crm_session` cookie (Max-Age=0)

No body.

---

## Current User

### `GET /api/v1/auth/me`

Return the authenticated user's profile. Used by the frontend on app load to restore session state.

**Auth**: Requires valid `crm_session` cookie.

**Response 200**
```json
{
  "id": 1,
  "email": "alice@example.com",
  "role": "admin",
  "display_name": "Alice Smith",
  "timezone": "America/New_York",
  "active": true,
  "locked": false
}
```

**Response 401** — Session expired or missing
```json
{
  "type": "https://crm.i2i.io/errors/session-expired",
  "title": "Session Expired",
  "status": 401,
  "detail": "Your session has expired. Please log in again."
}
```

---

## User Management (Admin only)

### `POST /api/v1/auth/users`

Create a new user account.

**Auth**: Admin role required.

**Request body**
```json
{
  "email": "bob@example.com",
  "password": "initial1234",
  "role": "sales_rep",
  "display_name": "Bob Jones"
}
```

**Response 201**
```json
{
  "id": 2,
  "email": "bob@example.com",
  "role": "sales_rep",
  "display_name": "Bob Jones",
  "active": true,
  "locked": false,
  "created_at": "2026-06-16T09:00:00Z"
}
```

**Errors**: 409 if email already exists; 422 if password < 8 chars or invalid role.

---

### `POST /api/v1/auth/users/{user_id}/reset-password`

Admin resets another user's password. Invalidates all existing sessions for that user.

**Auth**: Admin role required.

**Request body**
```json
{ "new_password": "newpass123" }
```

**Response 204** — No body. All existing sessions for `user_id` are deleted.

**Errors**: 403 if caller is not Admin; 404 if user not found; 422 if password too short.

---

### `POST /api/v1/auth/users/{user_id}/deactivate`

Admin deactivates a user account.

**Auth**: Admin role required.

**Response 204** — No body. User's active sessions are terminated. User can no longer log in.

**Errors**: 403 if caller is not Admin; 404 if user not found; 409 if attempting to deactivate the last active Admin.

---

### `POST /api/v1/auth/users/{user_id}/unlock`

Admin clears the `locked` flag.

**Auth**: Admin role required.

**Response 204** — No body. Resets `users.locked = false` and clears `failed_login_attempts` counter.

---

## Error Responses

All errors use RFC 7807 problem detail format.

| Status | Meaning |
|--------|---------|
| 401 | Missing/expired session or authentication failure |
| 403 | Caller lacks required role (e.g., non-Admin on admin endpoint) |
| 404 | User not found |
| 409 | Email already exists; or last Admin deactivation attempt |
| 422 | Validation failure (invalid email, short password, unknown role) |

**Security notes**:
- Rate limiting: `POST /auth/login` → max 20 requests per minute per IP (FastAPI middleware).
- The `crm_session` cookie is never returned in a JSON response body — only via `Set-Cookie` header.
- Expired sessions return 401 identically to missing sessions (no enumeration of session existence).
