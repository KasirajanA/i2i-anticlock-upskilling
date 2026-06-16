# Data Model: Contact & Account Management (Module 007)

**Date**: 2026-06-16 | **Feature**: 007-contact-management

---

## Entities

### Contact

Individual person record.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `first_name` | VARCHAR(100) | NOT NULL | |
| `last_name` | VARCHAR(100) | NOT NULL | |
| `email` | VARCHAR(254) | UNIQUE NOT NULL | Primary deduplication key; case-insensitive |
| `phone` | VARCHAR(30) | NULLABLE | |
| `job_title` | VARCHAR(100) | NULLABLE | |
| `primary_account_id` | INTEGER | FK → accounts.id NULLABLE | Primary linked account |
| `owner_id` | INTEGER | FK → users.id NULLABLE | Record owner |
| `tags` | JSON | default `[]` | Array of tag strings |
| `created_by_id` | INTEGER | FK → users.id NOT NULL | |
| `created_at` | DATETIME | NOT NULL, default NOW | |
| `updated_at` | DATETIME | NOT NULL, default NOW | |
| `deleted_at` | DATETIME | NULLABLE | Soft-delete timestamp |

**Indexes**: `(email)` UNIQUE, `(primary_account_id)`, `(owner_id)`, `(deleted_at)`

---

### ContactAccount

Many-to-many: one contact, multiple accounts.

| Column | Type | Constraints |
|--------|------|-------------|
| `contact_id` | INTEGER | FK → contacts.id NOT NULL |
| `account_id` | INTEGER | FK → accounts.id NOT NULL |
| `linked_at` | DATETIME | NOT NULL, default NOW |

**Primary Key**: `(contact_id, account_id)` composite

---

### Account

Company or organisation.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `name` | VARCHAR(255) | NOT NULL | |
| `industry` | VARCHAR(100) | NULLABLE | |
| `company_size` | VARCHAR(50) | NULLABLE | e.g., `"1-10"`, `"11-50"`, `"50-200"`, `"200+"` |
| `website` | VARCHAR(255) | NULLABLE | |
| `billing_address` | TEXT | NULLABLE | Free-form address |
| `owner_id` | INTEGER | FK → users.id NULLABLE | |
| `created_by_id` | INTEGER | FK → users.id NOT NULL | |
| `created_at` | DATETIME | NOT NULL, default NOW | |
| `updated_at` | DATETIME | NOT NULL, default NOW | |
| `deleted_at` | DATETIME | NULLABLE | Soft-delete ("archived") |

**Indexes**: `(name)`, `(owner_id)`, `(deleted_at)`

---

### Lead

Unqualified prospect managed by Sales Reps.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `first_name` | VARCHAR(100) | NOT NULL | |
| `last_name` | VARCHAR(100) | NOT NULL | |
| `email` | VARCHAR(254) | NOT NULL | |
| `company_name` | VARCHAR(255) | NULLABLE | |
| `status` | VARCHAR(20) | NOT NULL, default `new` | `new` \| `contacted` \| `qualified` \| `converted` \| `disqualified` |
| `disqualify_reason` | TEXT | NULLABLE | Required when status = `disqualified` |
| `notes` | TEXT | NULLABLE | Preserved on conversion to Contact |
| `owner_id` | INTEGER | FK → users.id NOT NULL | Must be Sales Rep or Admin |
| `converted_contact_id` | INTEGER | FK → contacts.id NULLABLE | Set on conversion |
| `created_at` | DATETIME | NOT NULL, default NOW | |
| `updated_at` | DATETIME | NOT NULL, default NOW | |
| `deleted_at` | DATETIME | NULLABLE | Set when disqualified (archived) |

**Indexes**: `(status, owner_id)`, `(email)`

---

### Segment

Named saved filter over contacts or accounts.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `name` | VARCHAR(100) | NOT NULL | |
| `entity_type` | VARCHAR(20) | NOT NULL | `contact` \| `account` |
| `filter_spec` | JSON | NOT NULL | Serialised filter conditions |
| `owner_id` | INTEGER | FK → users.id NOT NULL | |
| `created_at` | DATETIME | NOT NULL, default NOW | |
| `updated_at` | DATETIME | NOT NULL, default NOW | |

**Indexes**: `(owner_id, entity_type)`

---

### ActivityLog (per-record)

Unified append-only log for contacts, accounts, and leads.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `entity_type` | VARCHAR(20) | NOT NULL | `contact` \| `account` \| `lead` |
| `entity_id` | INTEGER | NOT NULL | |
| `event_type` | VARCHAR(30) | NOT NULL | `created`, `updated`, `archived`, `note_added`, `linked`, `converted` |
| `actor_id` | INTEGER | FK → users.id NULLABLE | |
| `metadata` | JSON | | Event-specific payload |
| `created_at` | DATETIME | NOT NULL, default NOW | |

**Indexes**: `(entity_type, entity_id, created_at)`

---

### CustomFieldDefinition

Admin-defined custom field schema.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | PK, autoincrement | |
| `entity_type` | VARCHAR(20) | NOT NULL | `contact` \| `account` |
| `field_key` | VARCHAR(50) | UNIQUE NOT NULL | Snake-case identifier |
| `label` | VARCHAR(100) | NOT NULL | Display label |
| `field_type` | VARCHAR(20) | NOT NULL | `text` \| `number` \| `date` \| `boolean` \| `select` |
| `options` | JSON | NULLABLE | For `select` type: list of allowed values |
| `required` | BOOLEAN | NOT NULL, default FALSE | |
| `created_by_id` | INTEGER | FK → users.id NOT NULL | |
| `created_at` | DATETIME | NOT NULL, default NOW | |

---

### CustomFieldValue

Per-record custom field values.

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | INTEGER | PK, autoincrement |
| `definition_id` | INTEGER | FK → custom_field_definitions.id NOT NULL |
| `entity_type` | VARCHAR(20) | NOT NULL |
| `entity_id` | INTEGER | NOT NULL |
| `field_value` | TEXT | NULLABLE |

**Indexes**: `(definition_id, entity_type, entity_id)` UNIQUE, `(entity_type, entity_id)`

---

## Relationships

```
Contact ─── many ──► ContactAccount ◄─── many ── Account
Contact ─── many ──► ActivityLog
Contact ─── 1    ──► Account (primary_account_id, nullable)
Account ─── many ──► ActivityLog
Lead    ─── many ──► ActivityLog
Lead    ─── 1    ──► Contact (converted_contact_id, nullable)

CustomFieldDefinition ─── many ──► CustomFieldValue
```

---

## Validation Rules

- `Contact.email`: required, valid format, globally unique (case-insensitive, normalised to lowercase)
- `Contact.first_name`, `last_name`: required, 1–100 characters
- `Lead.status` lifecycle: `new → contacted → qualified → converted / disqualified`; no backward transitions except by Admin
- `Lead.disqualify_reason`: required when `status = 'disqualified'`
- `Segment.filter_spec`: max 5 conditions; each condition must reference a valid field
- `CustomFieldDefinition.field_key`: snake_case, 3–50 chars, unique per `entity_type`
- `CustomFieldValue.field_value`: validated against `field_type` on write (`number` → parseable float, `date` → ISO8601 date, `boolean` → `"true"` / `"false"`, `select` → value in `options`)
