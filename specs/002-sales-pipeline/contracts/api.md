# API Contracts: Sales Pipeline

**Module**: 002 - Sales Pipeline
**Base URL**: `/api/v1`
**Auth**: All endpoints require a valid HTTP-only session cookie (`session_id`). Unauthenticated requests return `401`.

---

## Shared Error Schema

```json
{
  "detail": "Human-readable message",
  "code": "MACHINE_READABLE_CODE",
  "field": "field_name_if_applicable"
}
```

Common error codes:

| HTTP | code                  | Meaning                                        |
|------|-----------------------|------------------------------------------------|
| 400  | `VALIDATION_ERROR`    | Request body or query param failed validation  |
| 401  | `NOT_AUTHENTICATED`   | No valid session cookie                        |
| 403  | `FORBIDDEN`           | Authenticated but insufficient role/ownership  |
| 404  | `NOT_FOUND`           | Resource does not exist or is not visible      |
| 409  | `CONFLICT`            | Duplicate ref_id or unique constraint violation|
| 422  | `TERMINAL_STAGE`      | Attempt to change stage on a closed deal       |
| 422  | `LOSS_REASON_REQUIRED`| Closing Lost without providing loss_reason     |

---

## Endpoints

---

### GET /api/v1/deals

List deals with optional filters.

**Auth / Role**: Any authenticated user. Sales Reps see only team-scoped deals; Admins and Managers see all.

**Query Parameters**:

| Param      | Type    | Required | Description                                      |
|------------|---------|----------|--------------------------------------------------|
| stage      | string  | No       | Filter by pipeline stage enum value              |
| owner      | integer | No       | Filter by owner user ID                          |
| account_id | integer | No       | Filter by linked account ID                      |
| is_overdue | boolean | No       | `true` returns only overdue deals                |
| page       | integer | No       | Page number, default 1                           |
| limit      | integer | No       | Page size, default 25, max 100                   |

**Response 200**:

```json
{
  "total": 42,
  "page": 1,
  "limit": 25,
  "items": [
    {
      "id": 1,
      "ref_id": "DEAL-0001",
      "title": "Acme Corp Expansion",
      "value": "15000.00",
      "stage": "Proposal",
      "expected_close_date": "2026-07-31",
      "is_overdue": false,
      "is_archived": false,
      "owner": { "id": 3, "name": "Jane Smith" },
      "account": { "id": 7, "name": "Acme Corp", "is_archived": false },
      "contact": { "id": 12, "name": "Bob Jones" },
      "created_at": "2026-06-01T09:00:00Z",
      "updated_at": "2026-06-10T14:22:00Z"
    }
  ]
}
```

**Notable 4xx**: `403` if a Sales Rep supplies `owner` ID outside their team(s).

---

### POST /api/v1/deals

Create a new deal.

**Auth / Role**: Sales Rep, Manager, Admin.

**Request Body**:

```json
{
  "title": "Acme Corp Expansion",
  "value": 15000.00,
  "stage": "Lead In",
  "expected_close_date": "2026-07-31",
  "owner_id": 3,
  "account_id": 7,
  "contact_id": 12
}
```

| Field               | Type    | Required | Notes                                           |
|---------------------|---------|----------|-------------------------------------------------|
| title               | string  | Yes      |                                                 |
| value               | decimal | Yes      | >= 0                                            |
| stage               | string  | Yes      | Must be valid stage enum                        |
| expected_close_date | date    | Yes      | ISO 8601 `YYYY-MM-DD`                           |
| owner_id            | integer | Yes      | Sales Reps may only assign to themselves or teammates |
| account_id          | integer | Yes      |                                                 |
| contact_id          | integer | No       |                                                 |

**Response 201**:

```json
{
  "id": 1,
  "ref_id": "DEAL-0001",
  "title": "Acme Corp Expansion",
  "value": "15000.00",
  "stage": "Lead In",
  "expected_close_date": "2026-07-31",
  "is_overdue": false,
  "is_archived": false,
  "owner": { "id": 3, "name": "Jane Smith" },
  "account": { "id": 7, "name": "Acme Corp", "is_archived": false },
  "contact": { "id": 12, "name": "Bob Jones" },
  "created_at": "2026-06-16T10:00:00Z",
  "updated_at": "2026-06-16T10:00:00Z"
}
```

**Notable 4xx**: `400` if `account_id` references an unknown account; `403` if Sales Rep assigns to an owner outside their team.

---

### GET /api/v1/deals/{ref_id}

Fetch a single deal by reference ID.

**Auth / Role**: Any authenticated user subject to team-scoping for Sales Reps.

**Path Parameter**: `ref_id` — e.g., `DEAL-0001`

**Response 200**: Same shape as a single item from the list endpoint, plus full owner/account/contact objects.

**Notable 4xx**: `404` if deal does not exist or is outside the requester's visibility.

---

### PATCH /api/v1/deals/{ref_id}

Update editable fields on a deal.

**Auth / Role**: Owner (Sales Rep), Manager, Admin. Sales Reps cannot edit deals they do not own.

**Path Parameter**: `ref_id`

**Request Body** (all fields optional, at least one required):

```json
{
  "title": "Acme Corp — Phase 2",
  "value": 18000.00,
  "expected_close_date": "2026-08-15",
  "owner_id": 5,
  "account_id": 7,
  "contact_id": 14
}
```

**Response 200**: Updated deal object (same shape as GET).

**Notable 4xx**: `403` if Sales Rep attempts to edit another rep's deal; `404` if deal not found.

---

### POST /api/v1/deals/{ref_id}/stage

Change the pipeline stage of a deal.

**Auth / Role**: Owner (Sales Rep), Manager, Admin.

**Path Parameter**: `ref_id`

**Request Body**:

```json
{
  "stage": "Negotiation",
  "loss_reason": null
}
```

`loss_reason` is **required** (non-null, non-empty string) when `stage` is `"Closed Lost"`.

**Response 200**:

```json
{
  "ref_id": "DEAL-0001",
  "previous_stage": "Proposal",
  "new_stage": "Negotiation",
  "is_overdue": false,
  "updated_at": "2026-06-16T11:05:00Z"
}
```

**Notable 4xx**:
- `422` with code `TERMINAL_STAGE` if current stage is already Closed Won or Closed Lost.
- `422` with code `LOSS_REASON_REQUIRED` if `stage` is `"Closed Lost"` and `loss_reason` is absent or empty.

---

### GET /api/v1/deals/{ref_id}/comments

List comments on a deal.

**Auth / Role**: Any user who can view the deal.

**Path Parameter**: `ref_id`

**Query Parameters**:

| Param | Type    | Required | Description               |
|-------|---------|----------|---------------------------|
| page  | integer | No       | Default 1                 |
| limit | integer | No       | Default 25, max 100       |

**Response 200**:

```json
{
  "total": 3,
  "page": 1,
  "limit": 25,
  "items": [
    {
      "id": 101,
      "author": { "id": 3, "name": "Jane Smith" },
      "body": "Proposal sent to procurement team.",
      "created_at": "2026-06-10T09:30:00Z"
    }
  ]
}
```

---

### POST /api/v1/deals/{ref_id}/comments

Add a comment to a deal.

**Auth / Role**: Any user who can view the deal.

**Path Parameter**: `ref_id`

**Request Body**:

```json
{
  "body": "Follow-up call scheduled for Friday."
}
```

**Response 201**:

```json
{
  "id": 102,
  "author": { "id": 3, "name": "Jane Smith" },
  "body": "Follow-up call scheduled for Friday.",
  "created_at": "2026-06-16T11:10:00Z"
}
```

**Notable 4xx**: `400` if `body` is empty or whitespace-only.

---

### GET /api/v1/deals/{ref_id}/activity

Retrieve the full activity log for a deal, ordered by `created_at` ascending.

**Auth / Role**: Any user who can view the deal.

**Path Parameter**: `ref_id`

**Response 200**:

```json
{
  "total": 5,
  "items": [
    {
      "id": 201,
      "action_type": "deal_created",
      "actor": { "id": 3, "name": "Jane Smith" },
      "note": null,
      "created_at": "2026-06-01T09:00:00Z"
    },
    {
      "id": 202,
      "action_type": "stage_changed",
      "actor": { "id": 3, "name": "Jane Smith" },
      "note": "Lead In → Qualified",
      "created_at": "2026-06-05T14:00:00Z"
    }
  ]
}
```

---

### GET /api/v1/pipeline/forecast

Return stage-grouped pipeline totals with weighted forecast values and a Closed Won summary.

**Auth / Role**: Manager, Admin. Sales Reps receive `403`.

**Query Parameters**:

| Param  | Type   | Required | Description                                                      |
|--------|--------|----------|------------------------------------------------------------------|
| period | string | No       | ISO date range `YYYY-MM-DD/YYYY-MM-DD`. Defaults to current quarter. |

**Response 200**:

```json
{
  "period": {
    "start": "2026-07-01",
    "end": "2026-09-30"
  },
  "open_pipeline": [
    {
      "stage": "Lead In",
      "deal_count": 8,
      "total_value": "40000.00",
      "probability": 0.10,
      "weighted_value": "4000.00"
    },
    {
      "stage": "Qualified",
      "deal_count": 5,
      "total_value": "75000.00",
      "probability": 0.25,
      "weighted_value": "18750.00"
    },
    {
      "stage": "Proposal",
      "deal_count": 3,
      "total_value": "60000.00",
      "probability": 0.50,
      "weighted_value": "30000.00"
    },
    {
      "stage": "Negotiation",
      "deal_count": 2,
      "total_value": "50000.00",
      "probability": 0.75,
      "weighted_value": "37500.00"
    }
  ],
  "closed_won": {
    "deal_count": 4,
    "total_value": "92000.00"
  },
  "total_weighted_forecast": "90250.00"
}
```

**Notable 4xx**: `400` if `period` format is invalid; `403` if requester is a Sales Rep or Support Agent.
