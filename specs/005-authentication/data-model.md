# Data Model: Authentication (Module 005)

**Date**: 2026-06-16 | **Feature**: 005-authentication

---

## Entities

### User

Core identity record. Shared with Module 006 (User & Team Management), which extends it with profile fields.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `email` | VARCHAR(254) | UNIQUE NOT NULL | Normalised to lowercase on write; serves as username |
| `password_hash` | VARCHAR(100) | NOT NULL | bcrypt cost 12 |
| `role` | VARCHAR(20) | NOT NULL | `admin` \| `manager` \| `sales_rep` \| `support_agent` |
| `active` | BOOLEAN | NOT NULL, default TRUE | Admin-controlled; inactive users cannot log in |
| `locked` | BOOLEAN | NOT NULL, default FALSE | Security lockout (independent of `active`) |
| `created_at` | DATETIME | NOT NULL, default NOW | |
| `updated_at` | DATETIME | NOT NULL, default NOW | |

**Indexes**: `(email)` UNIQUE, `(role)`

**Note**: Module 006 adds `display_name`, `avatar_url`, `timezone` to this table. Auth and User Mgmt share the same ORM model.

---

### Session

Server-side session record.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `session_id` | VARCHAR(36) | PK | UUID4, opaque token sent to client |
| `user_id` | INTEGER | FK → users.id NOT NULL | |
| `created_at` | DATETIME | NOT NULL, default NOW | |
| `last_active_at` | DATETIME | NOT NULL, default NOW | Updated on every authenticated request |
| `expires_at` | DATETIME | NOT NULL | `created_at + 30 min`; extended via `last_active_at` check |

**Indexes**: `(user_id)`, `(last_active_at)` (for expiry job cleanup)

**Expiry check**: `last_active_at < NOW() - INTERVAL 30 MINUTES` — checked in middleware on every request.

---

### FailedLoginAttempt

Per-username counter for lockout enforcement.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `email` | VARCHAR(254) | NOT NULL | Normalised lowercase |
| `attempt_count` | INTEGER | NOT NULL, default 1 | |
| `last_attempt_at` | DATETIME | NOT NULL, default NOW | |
| `locked_at` | DATETIME | NULLABLE | Set when attempt_count reaches 5 |

**Indexes**: `(email)` UNIQUE

---

## Relationships

```
User ─── many ──► Session
User ─── 1    ──► FailedLoginAttempt  (via email, upserted on each failed login)
```

---

## State Diagram — User Account States

```
        [Active + Unlocked]  ◄────── Admin clears `locked`
               │ │
     5 failures│ │Admin deactivates
               ▼ ▼
        [Active + Locked]   [Inactive + Unlocked]
                │                    │
           Admin unlocks       Admin reactivates
                │                    │
                └─────► [Active + Unlocked]
```

`active=False` prevents login regardless of `locked`.  
`locked=True` prevents login regardless of `active`.

---

## Session Lifecycle

```
Login → INSERT sessions (session_id=UUID4, last_active_at=NOW)
           │
     Every request → UPDATE sessions SET last_active_at=NOW WHERE session_id=:sid
           │
     Request check: IF last_active_at < NOW()-30min → HTTP 401, client redirects
           │
     Logout / Admin reset → DELETE FROM sessions WHERE session_id=:sid (or user_id=:uid)
           │
     Cleanup job (hourly) → DELETE FROM sessions WHERE last_active_at < NOW()-30min
```

---

## Validation Rules

- `email`: required, valid RFC 5322 format, max 254 chars, normalised to lowercase before uniqueness check
- `password` (at creation/reset): minimum 8 characters; no other complexity rules in v1
- `role`: must be one of `admin`, `manager`, `sales_rep`, `support_agent`
- Login: generic 401 for any failure (no enumeration); bcrypt dummy run when user not found
- Lockout: triggered after exactly 5 consecutive failures; counter reset on successful login
- `locked` flag: cleared only by Admin; `active` flag: set only by Admin
