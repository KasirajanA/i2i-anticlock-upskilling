# API Contract: User & Team Management (Module 006)

**Base path**: `/api/v1`  
**Auth**: `crm_session` cookie required on all endpoints  
**Content-Type**: `application/json` (except avatar upload: `multipart/form-data`)

---

## User List & Detail

### `GET /api/v1/users`

List all users. Admin only.

**Query parameters**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `role` | string | — | Filter by role |
| `active` | boolean | — | Filter by active status |
| `q` | string | — | Search by display name or email |

**Response 200**
```json
{
  "items": [
    {
      "id": 1,
      "email": "alice@example.com",
      "display_name": "Alice Smith",
      "role": "admin",
      "active": true,
      "locked": false,
      "timezone": "America/New_York",
      "avatar_url": "/static/avatars/1.webp",
      "created_at": "2026-06-15T08:00:00Z"
    }
  ],
  "total": 12
}
```

---

### `GET /api/v1/users/{user_id}`

Get a single user. Admin only (for other users); any user for their own profile.

**Response 200**: Same schema as list item.

---

### `PATCH /api/v1/users/{user_id}`

Update user profile. Admin can update any user's `role`, `active`. Users can update their own `display_name`, `timezone`.

**Request body** (all fields optional)
```json
{
  "display_name": "Alice S.",
  "timezone": "Europe/London",
  "role": "manager"
}
```

**Response 200**: Updated user object.

**Errors**: 403 if non-Admin tries to change `role` or other users' data; 422 if invalid timezone or role.

---

## Profile — Own Account

### `GET /api/v1/users/me`

Get the authenticated user's own profile. Alias for `GET /api/v1/users/{own_id}`.

**Response 200**: Full user object including `timezone`, `avatar_url`.

---

### `PATCH /api/v1/users/me`

Update own profile (display name, timezone).

**Request body**
```json
{
  "display_name": "Alice S.",
  "timezone": "Europe/London"
}
```

**Response 200**: Updated user object.

---

### `POST /api/v1/users/me/change-password`

Change own password. Requires current password confirmation.

**Request body**
```json
{
  "current_password": "old_password",
  "new_password": "new_password_123"
}
```

**Response 204** — No body. Existing sessions (except current) are not invalidated.

**Errors**: 401 if `current_password` incorrect; 422 if `new_password` too short.

---

### `POST /api/v1/users/me/avatar`

Upload a profile avatar.

**Content-Type**: `multipart/form-data`

**Form field**: `file` — image file (JPEG, PNG, or WEBP), max 2 MB.

**Response 200**
```json
{ "avatar_url": "/static/avatars/1.webp" }
```

**Errors**: 422 if file exceeds 2 MB, unsupported MIME type, or not an image.

---

## Team Management (Admin only)

### `GET /api/v1/teams`

List all teams.

**Response 200**
```json
{
  "items": [
    {
      "id": 1,
      "name": "EMEA Sales",
      "lead": { "id": 5, "display_name": "Alice Smith" },
      "member_count": 8,
      "created_at": "2026-06-15T08:00:00Z"
    }
  ],
  "total": 3
}
```

---

### `POST /api/v1/teams`

Create a new team. Admin only.

**Request body**
```json
{
  "name": "EMEA Sales",
  "lead_user_id": 5,
  "member_ids": [5, 7, 9]
}
```

**Response 201**: Created team object with members.

**Errors**: 409 if team name already exists; 422 if `lead_user_id` not in `member_ids`.

---

### `GET /api/v1/teams/{team_id}`

Get a team with its full member list.

**Response 200**
```json
{
  "id": 1,
  "name": "EMEA Sales",
  "lead": { "id": 5, "display_name": "Alice Smith" },
  "members": [
    { "id": 5, "display_name": "Alice Smith", "role": "sales_rep" },
    { "id": 7, "display_name": "Bob Jones",   "role": "sales_rep" }
  ],
  "created_at": "2026-06-15T08:00:00Z"
}
```

---

### `PATCH /api/v1/teams/{team_id}`

Update team name or lead. Admin only.

**Request body** (all fields optional)
```json
{
  "name": "EMEA & APAC Sales",
  "lead_user_id": 7
}
```

**Response 200**: Updated team object.

---

### `POST /api/v1/teams/{team_id}/members`

Add members to a team. Admin only.

**Request body**
```json
{ "user_ids": [11, 13] }
```

**Response 204** — No body.

---

### `DELETE /api/v1/teams/{team_id}/members/{user_id}`

Remove a member from a team. Admin only. If removed user is the team lead, `lead_user_id` is cleared.

**Response 204** — No body.

---

## Error Responses

| Status | Meaning |
|--------|---------|
| 401 | Session expired |
| 403 | Insufficient role (non-Admin accessing admin-only endpoint) |
| 404 | User or team not found |
| 409 | Team name duplicate; last Admin deactivation attempt |
| 413 | Avatar file exceeds 2 MB |
| 422 | Invalid timezone, role, or validation failure |
