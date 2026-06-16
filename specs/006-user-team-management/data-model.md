# Data Model: User & Team Management (Module 006)

**Date**: 2026-06-16 | **Feature**: 006-user-team-management

---

## Entities

### User (extended from Module 005)

Module 006 adds profile columns to the existing `users` table via additive migration.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| **[Module 005 columns — auth]** | | | |
| `id` | INTEGER | PK | |
| `email` | VARCHAR(254) | UNIQUE NOT NULL | |
| `password_hash` | VARCHAR(100) | NOT NULL | |
| `role` | VARCHAR(20) | NOT NULL | `admin` \| `manager` \| `sales_rep` \| `support_agent` |
| `active` | BOOLEAN | NOT NULL, default TRUE | |
| `locked` | BOOLEAN | NOT NULL, default FALSE | |
| `created_at` | DATETIME | NOT NULL | |
| `updated_at` | DATETIME | NOT NULL | |
| **[Module 006 columns — profile]** | | | |
| `display_name` | VARCHAR(100) | NULLABLE | Defaults to email prefix until set |
| `avatar_url` | VARCHAR(255) | NULLABLE | Path to uploaded avatar file |
| `timezone` | VARCHAR(64) | NULLABLE, default `"UTC"` | IANA tz string, validated on write |

---

### Team

Named group of users.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `name` | VARCHAR(100) | UNIQUE NOT NULL | |
| `lead_user_id` | INTEGER | FK → users.id NULLABLE, ON DELETE SET NULL | Optional designated lead |
| `created_by_id` | INTEGER | FK → users.id NOT NULL | |
| `created_at` | DATETIME | NOT NULL, default NOW | |
| `updated_at` | DATETIME | NOT NULL, default NOW | |

**Indexes**: `(name)` UNIQUE, `(lead_user_id)`

---

### TeamMember

Many-to-many join table.

| Column | Type | Constraints |
|--------|------|-------------|
| `team_id` | INTEGER | FK → teams.id NOT NULL |
| `user_id` | INTEGER | FK → users.id NOT NULL |
| `joined_at` | DATETIME | NOT NULL, default NOW |

**Primary Key**: `(team_id, user_id)` composite

**Indexes**: `(user_id)` (for "which teams does a user belong to?")

---

## Role Matrix (in-code, not persisted)

```python
MODULE_PERMISSIONS: dict[str, set[str]] = {
    "user_team_management":  {"admin"},
    "contact_management":    {"admin", "manager", "sales_rep", "support_agent"},
    "sales_pipeline":        {"admin", "manager", "sales_rep"},
    "contract_management":   {"admin", "manager", "sales_rep"},
    "customer_support":      {"admin", "manager", "support_agent"},
    "analytics_reporting":   {"admin", "manager", "sales_rep", "support_agent"},
}

# Write access within a module (subset of above)
MODULE_WRITE_PERMISSIONS: dict[str, set[str]] = {
    "contact_management":   {"admin", "sales_rep"},
    "sales_pipeline":       {"admin", "sales_rep"},
    "contract_management":  {"admin", "sales_rep"},
    "customer_support":     {"admin", "support_agent"},
    "analytics_reporting":  set(),  # read-only for all
}
```

---

## Relationships

```
User ─── many ──► TeamMember ◄─── many ── Team
Team ──── 1  ──► User (lead, nullable)
User ──── 1  ──► Team (created_by)
```

---

## Validation Rules

- `display_name`: optional, 1–100 characters
- `avatar_url`: set by server after upload; not writable by client directly
- `timezone`: must be a valid IANA timezone string; validated via `zoneinfo.available_timezones()`
- `role`: one of the four fixed values; only Admin may change it
- `Team.name`: required, 1–100 characters, unique
- `Team.lead_user_id`: if set, must be a member of the team; enforced in `TeamService`
- Self-role-change: users cannot change their own role
- Last Admin guard: deactivation of the last active Admin raises HTTP 409

---

## Avatar Storage (local, MVP)

```text
storage/
└── avatars/
    └── {user_id}.webp    # 200×200 px, WEBP format, max 2 MB input
```

Served at `/static/avatars/{user_id}.webp` via FastAPI `StaticFiles`.
