# API Contracts: Notifications & Alerts (Module 008)

**Base URL**: `/api/v1`
**Auth**: Bearer token (session cookie) on all endpoints except `/sse` (query-param token for EventSource compatibility).
**Content-Type**: `application/json` unless noted.

---

## Notifications

### GET /notifications

Paginated list of the current user's notifications (cursor-based, newest first).

**Query params**:
| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `limit` | int | 20 | Max 50 |
| `cursor` | int | (none) | Last `id` from previous page for infinite scroll |
| `unread_only` | bool | false | Filter to unread only |

**Response 200**:
```json
{
  "items": [
    {
      "id": 42,
      "event_type": "assignment",
      "title": "Deal #DEAL-0012 assigned to you",
      "body": null,
      "source_record_type": "deal",
      "source_record_id": 12,
      "is_read": false,
      "is_digest": false,
      "digest_count": 1,
      "created_at": "2026-06-16T10:30:00Z"
    }
  ],
  "next_cursor": 21,
  "unread_count": 5
}
```

---

### GET /notifications/unread-count

Returns just the badge count for the bell icon.

**Response 200**:
```json
{ "count": 5 }
```

---

### PATCH /notifications/{id}/read

Mark a single notification as read.

**Response 200**:
```json
{ "id": 42, "is_read": true }
```

**Response 404**: Notification not found or not owned by current user.

---

### POST /notifications/mark-all-read

Mark all unread notifications as read for the current user.

**Response 200**:
```json
{ "updated_count": 5 }
```

---

## Server-Sent Events

### GET /sse

Opens an SSE stream for the authenticated user. Requires `token` query param (session token) because `EventSource` cannot set `Authorization` headers.

**Query params**: `token` (required), `last_event_id` (optional, for replay on reconnect).

**Response**: `text/event-stream`

**Event types emitted**:
```
event: notification.new
data: {"id": 42, "event_type": "assignment", "title": "...", "unread_count": 6}

event: notification.refresh
data: {"unread_count": 3}

event: ping
data: {}
```

- `notification.new` — new individual notification; client prepends to list.
- `notification.refresh` — count changed (e.g., after digest flush); client refetches.
- `ping` — keep-alive every 30 s; client ignores.

---

## Notification Preferences

### GET /preferences/notifications

Get all notification preferences for the current user. Returns one entry per event type; missing entries are treated as `is_enabled: true` by the server.

**Response 200**:
```json
{
  "preferences": [
    { "event_type": "assignment", "is_enabled": true },
    { "event_type": "comment", "is_enabled": false },
    { "event_type": "mention", "is_enabled": true },
    { "event_type": "status_change", "is_enabled": true },
    { "event_type": "contract_renewal_due", "is_enabled": true },
    { "event_type": "deal_stage_change", "is_enabled": false },
    { "event_type": "sla_breach", "is_enabled": true }
  ]
}
```

---

### PUT /preferences/notifications

Upsert notification preferences (all at once).

**Request body**:
```json
{
  "preferences": [
    { "event_type": "comment", "is_enabled": false },
    { "event_type": "deal_stage_change", "is_enabled": false }
  ]
}
```

**Response 200**: Same shape as GET.

**Validation errors 422**: Unknown `event_type`, duplicate entries in payload.

---

## Admin Notification Rules

All endpoints in this group require **Admin** role. Returns 403 for other roles.

### GET /admin/notification-rules

List all Admin notification rules.

**Response 200**:
```json
{
  "rules": [
    {
      "id": 1,
      "name": "High-value deal alert",
      "event_type": "deal_stage_change",
      "filter_field": "deal_value",
      "filter_operator": ">",
      "filter_value": "10000",
      "target_type": "role",
      "target_value": "Admin",
      "is_enabled": true,
      "created_at": "2026-06-16T09:00:00Z"
    }
  ]
}
```

---

### POST /admin/notification-rules

Create a new Admin notification rule.

**Request body**:
```json
{
  "name": "Critical SLA breach to Admins",
  "event_type": "sla_breach",
  "filter_field": "priority",
  "filter_operator": "=",
  "filter_value": "Critical",
  "target_type": "role",
  "target_value": "Admin"
}
```

**Validation**: `filter_field/operator/value` must all be present or all absent. `target_type` = `user` requires `target_value` to be a valid user ID string.

**Response 201**: Rule object.

---

### PATCH /admin/notification-rules/{id}

Enable, disable, or update a rule.

**Request body** (partial update):
```json
{ "is_enabled": false }
```

**Response 200**: Updated rule object.

**Side effect**: Rule cache in `RuleEngine` is invalidated and reloaded.

---

### DELETE /admin/notification-rules/{id}

Delete a rule. Past notifications triggered by this rule are retained (`admin_rule_id` set to NULL).

**Response 204**: No content.

---

## Error Schema

All error responses:
```json
{
  "detail": "Human-readable message",
  "code": "MACHINE_CODE"
}
```

Common codes: `NOT_FOUND`, `FORBIDDEN`, `VALIDATION_ERROR`, `INVALID_EVENT_TYPE`, `INVALID_OPERATOR`.
