# API Contract: Customer Support (Module 003)

**Base path**: `/api/v1/support`  
**Auth**: Bearer token required on all endpoints (session cookie or `Authorization: Bearer <token>`)  
**Content-Type**: `application/json`

---

## Tickets

### `GET /api/v1/support/tickets`

List tickets with optional filters. Role-scoped: agents see only assigned + unassigned tickets; admins see all.

**Query parameters**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | string | — | Filter by status: `open`, `in_progress`, `resolved`, `closed` |
| `priority` | string | — | Filter by priority: `low`, `medium`, `high`, `critical` |
| `assignee_id` | integer | — | Filter by assignee user ID |
| `account_id` | integer | — | Filter by linked account |
| `created_after` | ISO8601 | — | Date range start |
| `created_before` | ISO8601 | — | Date range end |
| `queue` | string | — | `mine` (assigned to me) \| `unassigned` \| `all` (admin only) |
| `cursor` | string | — | Pagination cursor (opaque, from previous response) |
| `limit` | integer | 50 | Max 100 |

**Response 200**
```json
{
  "items": [
    {
      "id": 1,
      "ref": "I2I-CRM-0001",
      "subject": "Login page broken",
      "status": "open",
      "priority": "high",
      "contact_name": "Jane Doe",
      "account_name": "Acme Corp",
      "assignee": { "id": 5, "display_name": "Alice Smith" },
      "sla": {
        "first_response_due": "2026-06-17T10:00:00Z",
        "resolution_due": "2026-06-18T10:00:00Z",
        "first_response_breached": false,
        "resolution_breached": false,
        "warning": false
      },
      "created_at": "2026-06-16T09:00:00Z",
      "updated_at": "2026-06-16T09:30:00Z"
    }
  ],
  "next_cursor": "eyJpZCI6MTAwfQ==",
  "total": 247
}
```

---

### `POST /api/v1/support/tickets`

Create a new ticket. Accessible by support agents and admins.

**Request body**
```json
{
  "subject": "Login page broken",
  "description": "Users cannot log in since the 3pm deployment.",
  "priority": "high",
  "contact_id": 42,
  "assignee_id": 5
}
```

**Response 201**
```json
{
  "id": 1,
  "ref": "I2I-CRM-0001",
  "subject": "Login page broken",
  "status": "open",
  "priority": "high",
  "contact_id": 42,
  "contact_name_snapshot": "Jane Doe",
  "account_id": 7,
  "assignee_id": 5,
  "created_by_id": 3,
  "created_at": "2026-06-16T09:00:00Z",
  "updated_at": "2026-06-16T09:00:00Z"
}
```

**Errors**: 422 if `contact_id` missing or invalid; 403 if caller lacks support role.

---

### `GET /api/v1/support/tickets/{ticket_id}`

Retrieve a single ticket with its latest SLA record.

**Response 200**
```json
{
  "id": 1,
  "ref": "I2I-CRM-0001",
  "subject": "Login page broken",
  "description": "Users cannot log in...",
  "status": "open",
  "priority": "high",
  "contact_id": 42,
  "contact_name_snapshot": "Jane Doe",
  "account_id": 7,
  "assignee_id": 5,
  "created_by_id": 3,
  "sla": {
    "cycle": 1,
    "first_response_due": "2026-06-17T10:00:00Z",
    "resolution_due": "2026-06-18T10:00:00Z",
    "first_response_at": null,
    "resolved_at": null,
    "first_response_breached": false,
    "resolution_breached": false
  },
  "created_at": "2026-06-16T09:00:00Z",
  "updated_at": "2026-06-16T09:00:00Z"
}
```

---

### `PATCH /api/v1/support/tickets/{ticket_id}`

Update ticket fields. Status transitions are validated server-side.

**Request body** (all fields optional)
```json
{
  "status": "in_progress",
  "assignee_id": 5,
  "priority": "critical"
}
```

**Response 200**: Updated ticket object (same schema as GET).

**Errors**: 422 on invalid status transition; 403 if agent tries to revert status.

---

### `POST /api/v1/support/tickets/{ticket_id}/assign`

Assign or reassign a ticket. Accessible by agents (self-assign only) and admins.

**Request body**
```json
{ "assignee_id": 5 }
```

**Response 200**: Updated ticket object.

---

## Replies & Notes

### `GET /api/v1/support/tickets/{ticket_id}/replies`

List all replies for a ticket. Internal notes filtered out for non-agent roles.

**Response 200**
```json
{
  "items": [
    {
      "id": 1,
      "ticket_id": 1,
      "author": { "id": 5, "display_name": "Alice Smith" },
      "body": "We are investigating this issue.",
      "is_internal": false,
      "created_at": "2026-06-16T09:30:00Z"
    }
  ]
}
```

---

### `POST /api/v1/support/tickets/{ticket_id}/replies`

Add a reply or internal note. If ticket is `Resolved`, triggers automatic re-open.

**Request body**
```json
{
  "body": "We have identified the root cause.",
  "is_internal": false
}
```

**Response 201**: Created reply object.  
**Side effects**: If first non-internal reply and SLA not yet met, marks `first_response_at`. If ticket was `Resolved`, re-opens and creates a new `SLARecord`.

---

## Activity Log

### `GET /api/v1/support/tickets/{ticket_id}/activity`

Retrieve the full activity log for a ticket, newest first.

**Response 200**
```json
{
  "items": [
    {
      "id": 10,
      "event_type": "status_change",
      "actor": { "id": 5, "display_name": "Alice Smith" },
      "metadata": { "from": "open", "to": "in_progress" },
      "created_at": "2026-06-16T09:45:00Z"
    }
  ]
}
```

---

## SLA

### `GET /api/v1/support/tickets/{ticket_id}/sla`

List all SLA records for a ticket (all cycles).

**Response 200**
```json
{
  "items": [
    {
      "id": 1,
      "cycle": 1,
      "first_response_due": "2026-06-17T10:00:00Z",
      "resolution_due": "2026-06-18T10:00:00Z",
      "first_response_at": "2026-06-16T09:30:00Z",
      "resolved_at": null,
      "first_response_breached": false,
      "resolution_breached": false,
      "is_active": true
    }
  ]
}
```

---

## Error Responses

All errors follow the RFC 7807 problem detail format:

```json
{
  "type": "https://crm.i2i.io/errors/invalid-status-transition",
  "title": "Invalid Status Transition",
  "status": 422,
  "detail": "Agents cannot revert ticket status from 'in_progress' to 'open'."
}
```

| Status | Meaning |
|--------|---------|
| 401 | Missing or expired session |
| 403 | Insufficient role |
| 404 | Ticket not found |
| 422 | Validation error or invalid transition |
| 500 | Internal server error |
