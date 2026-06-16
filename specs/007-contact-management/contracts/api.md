# API Contract: Contact & Account Management (Module 007)

**Base path**: `/api/v1`  
**Auth**: `crm_session` cookie required on all endpoints  
**Content-Type**: `application/json` (except CSV import: `multipart/form-data`)

---

## Contacts

### `GET /api/v1/contacts`

List contacts with search and filter. Support Agents: read-only.

**Query parameters**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `q` | string | — | Full-text search: name or email |
| `account_id` | integer | — | Filter by linked account |
| `tag` | string | — | Filter by tag |
| `owner_id` | integer | — | Filter by record owner |
| `include_archived` | boolean | false | Include soft-deleted contacts |
| `cursor` | string | — | Pagination cursor |
| `limit` | integer | 50 | Max 100 |

**Response 200**
```json
{
  "items": [
    {
      "id": 1,
      "first_name": "Jane",
      "last_name": "Doe",
      "email": "jane@acme.com",
      "phone": "+1-555-1234",
      "job_title": "VP Engineering",
      "primary_account": { "id": 5, "name": "Acme Corp" },
      "tags": ["enterprise", "decision-maker"],
      "owner": { "id": 3, "display_name": "Alice Smith" },
      "created_at": "2026-06-15T08:00:00Z"
    }
  ],
  "next_cursor": "eyJpZCI6MTAwfQ==",
  "total": 1423
}
```

---

### `POST /api/v1/contacts`

Create a contact. Sales Rep and Admin only.

**Request body**
```json
{
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane@acme.com",
  "phone": "+1-555-1234",
  "job_title": "VP Engineering",
  "account_ids": [5],
  "primary_account_id": 5,
  "tags": ["enterprise"]
}
```

**Response 201**: Created contact object.

**Response 200 + `duplicate_warning`** (when email already exists)
```json
{
  "duplicate_warning": {
    "existing_id": 42,
    "existing_email": "jane@acme.com",
    "message": "A contact with this email already exists."
  }
}
```

**Errors**: 422 if required fields missing; 403 if Support Agent.

---

### `GET /api/v1/contacts/{contact_id}`

Get a single contact with custom fields and linked accounts.

**Response 200**
```json
{
  "id": 1,
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane@acme.com",
  "accounts": [
    { "id": 5, "name": "Acme Corp", "is_archived": false }
  ],
  "custom_fields": [
    { "key": "contract_tier", "label": "Contract Tier", "value": "enterprise" }
  ],
  "created_at": "2026-06-15T08:00:00Z",
  "updated_at": "2026-06-16T09:00:00Z"
}
```

---

### `PATCH /api/v1/contacts/{contact_id}`

Update a contact. Sales Rep (own records) and Admin.

**Request body** (all fields optional)
```json
{
  "job_title": "CTO",
  "tags": ["enterprise", "technical-buyer"]
}
```

**Response 200**: Updated contact.

---

### `DELETE /api/v1/contacts/{contact_id}`

Soft-archive a contact. Admin only. Sets `deleted_at`. Linked tickets retain the name snapshot.

**Response 204** — No body.

---

## Contact CSV Import

### `POST /api/v1/contacts/import`

Bulk import contacts from CSV. Sales Rep and Admin only.

**Content-Type**: `multipart/form-data`

**Form fields**:
- `file`: CSV file with header row
- `duplicate_mode`: `skip` (default) or `overwrite`

**Response 200**
```json
{
  "imported": 847,
  "skipped": 98,
  "errors": 5,
  "error_details": [
    { "row": 14, "reason": "Invalid email format: 'not-an-email'" }
  ]
}
```

---

## Accounts

### `GET /api/v1/accounts`

List accounts. Support Agents: read-only. Archived accounts excluded by default.

**Query parameters**: `q` (search by name), `industry`, `owner_id`, `include_archived`, `cursor`, `limit`

**Response 200**
```json
{
  "items": [
    {
      "id": 5,
      "name": "Acme Corp",
      "industry": "Technology",
      "company_size": "200+",
      "website": "https://acme.com",
      "contact_count": 12,
      "owner": { "id": 3, "display_name": "Alice Smith" },
      "is_archived": false,
      "created_at": "2026-06-01T08:00:00Z"
    }
  ],
  "next_cursor": null,
  "total": 34
}
```

---

### `POST /api/v1/accounts` / `GET /api/v1/accounts/{id}` / `PATCH /api/v1/accounts/{id}`

Standard CRUD following the same pattern as contacts.

---

### `GET /api/v1/accounts/{account_id}/timeline`

Unified timeline: contacts, deals, contracts, support tickets linked to this account.

**Response 200**
```json
{
  "items": [
    { "type": "contact",  "id": 1,  "label": "Jane Doe linked",          "created_at": "2026-06-15T08:00:00Z" },
    { "type": "deal",     "id": 7,  "label": "Deal: Q3 Renewal opened",  "created_at": "2026-06-10T10:00:00Z" },
    { "type": "ticket",   "id": 12, "label": "Ticket I2I-CRM-0012 opened","created_at": "2026-06-08T14:00:00Z" }
  ]
}
```

---

## Leads

### `GET /api/v1/leads` / `POST /api/v1/leads` / `PATCH /api/v1/leads/{id}`

Standard CRUD. Sales Rep manages own leads; Admin and Manager have read-only access; Support Agent has no access.

---

### `POST /api/v1/leads/{lead_id}/convert`

Convert a lead to Contact + (optionally) Account + (optionally) Deal. Atomic transaction.

**Request body**
```json
{
  "create_account": true,
  "create_deal": true,
  "deal_title": "Acme Q3 Deal",
  "deal_value": 45000
}
```

**Response 201**
```json
{
  "contact_id": 98,
  "account_id": 56,
  "deal_id": 34,
  "lead_id": 10,
  "status": "converted"
}
```

---

## Segments

### `GET /api/v1/segments` / `POST /api/v1/segments`

List and create named saved filters.

**POST request body**
```json
{
  "name": "Enterprise contacts in EMEA",
  "entity_type": "contact",
  "filter_spec": {
    "conditions": [
      { "field": "tag", "operator": "in", "value": ["enterprise"] },
      { "field": "account.industry", "operator": "eq", "value": "Technology" }
    ]
  }
}
```

**Response 201**
```json
{
  "id": 3,
  "name": "Enterprise contacts in EMEA",
  "entity_type": "contact",
  "live_count": 47,
  "created_at": "2026-06-16T09:00:00Z"
}
```

---

## Error Responses

| Status | Meaning |
|--------|---------|
| 401 | Session expired |
| 403 | Insufficient role |
| 404 | Contact, account, or lead not found |
| 409 | Duplicate email on contact creation |
| 422 | Validation failure (invalid email, missing required field) |
