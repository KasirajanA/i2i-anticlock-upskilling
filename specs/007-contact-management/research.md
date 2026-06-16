# Research: Contact & Account Management (Module 007)

**Date**: 2026-06-16 | **Feature**: 007-contact-management

---

## 1. Duplicate Contact Detection

**Decision**: Exact email-match check on every save (`SELECT id FROM contacts WHERE email = :email AND id != :current_id AND deleted_at IS NULL`). UI presents a warning + "View existing" link rather than blocking silently.

**Rationale**: FR-003 requires duplicate detection (same email) on every save. The spec confirms email is the primary deduplication key (no fuzzy name matching). Running the check inside the transaction prevents TOCTOU races under concurrent inserts (SQLite WAL serialises writes). The UI warns and offers a link; it does not block the create (user may intentionally override).

**Alternatives considered**: Unique DB constraint on email (would raise an unhandled IntegrityError instead of a friendly warning); fuzzy name matching (out of scope per clarification).

---

## 2. CSV Bulk Import

**Decision**: `POST /api/v1/contacts/import` accepts a CSV file (multipart/form-data). Backend streams the file line-by-line with `csv.DictReader`, validates each row, and applies the selected duplicate-resolution mode (`skip` or `overwrite`) per import run.

**Rationale**: FR-008 requires 1,000-contact import in ≤ 2 minutes (SC-004). Streaming avoids loading the entire file into memory. Rows are processed in batches of 100 using `AsyncSession.execute(insert(Contact).values(...))` bulk inserts. A result summary (`imported`, `skipped`, `errors`) is returned after the import completes.

**Alternatives considered**: Background job with status polling (adds complexity; 2-min limit is achievable synchronously for 1,000 rows); Pandas (heavy dependency, not justified for simple CSV parsing).

---

## 3. Saved Segments (Named Filters)

**Decision**: `Segment` entity stores a filter expression as a JSON blob (`filter_spec`). On segment retrieval, the backend deserialises `filter_spec` and reconstructs the SQL query dynamically using `FilterQueryBuilder`. Live count is computed via `SELECT COUNT(*)` using the same builder.

**Rationale**: FR-007 requires saved named filters. JSON storage is flexible for evolving filter criteria without schema migrations. `FilterQueryBuilder` centralises filter-to-SQL translation, ensuring the segment query is identical to the ad-hoc filtered list query (DRY). Maximum filter complexity is bounded: field `IN` (`name`, `email`, `account_id`, `tag`, `custom_field_key`), one operator per field, max 5 conditions.

**Alternatives considered**: EAV (entity-attribute-value) filter table (relational but query-complex); storing raw SQL (SQL injection risk); client-side filter (no server-side count).

---

## 4. Custom Fields

**Decision**: `CustomFieldDefinition` table (Admin-defined schema) + `CustomFieldValue` table (per-contact/account values). Field types: `text`, `number`, `date`, `boolean`, `select` (predefined options).

**Rationale**: FR-010 requires Admin-configurable custom fields. A separate value table avoids altering the contacts schema per field definition. `CustomFieldValue.field_value` is stored as TEXT; the type coercion is applied in `CustomFieldService.get_typed_value()`. Indexed on `(contact_id, definition_id)` for efficient read.

**Alternatives considered**: JSON column on `contacts` (flexible but hard to index/filter by custom field value); EAV with typed value columns (more columns, more joins).

---

## 5. Lead Conversion

**Decision**: `POST /api/v1/leads/{id}/convert` is atomic: in a single transaction, creates `Contact` (+ optionally `Account` + optionally `Deal`), copies `Lead.notes` to `Contact.activity_log`, sets `Lead.status = 'converted'`, and stores `Lead.converted_contact_id`.

**Rationale**: FR-006 requires single-operation conversion preserving all notes. Atomicity prevents partial conversion (e.g., Contact created but Deal failed). The audit link (`Lead.converted_contact_id`) satisfies the assumption that converted leads retain a link to the original lead record.

**Alternatives considered**: Multi-step wizard with client-managed state (complex rollback handling); separate convert job (async complexity for a synchronous user action).

---

## 6. Account Unified Timeline

**Decision**: `GET /api/v1/accounts/{id}/timeline` returns a merged, time-sorted list of contacts, deals, contracts, and support tickets linked to the account, fetched via `asyncio.gather()` across the respective tables.

**Rationale**: FR-004 requires unified account view across all modules. The query is read-only; parallel async queries via `asyncio.gather()` against SQLite keep latency low (no foreign-key JOINs required since each module owns its own table). Results are merged in Python and sorted by `created_at` descending.

**Alternatives considered**: Materialised activity feed table (adds write amplification across all modules); GraphQL (over-engineered for a single account view endpoint).

---

## 7. Contact Many-to-Many Accounts

**Decision**: `contact_accounts` join table (many-to-many); `contacts.primary_account_id` for the "main" account used in support ticket auto-fill.

**Rationale**: Spec assumption: a contact may be linked to multiple accounts (consultant scenario). A join table handles this. `primary_account_id` is a shortcut for the most common use case (ticket creation auto-fills account from contact's primary). If no primary is set, the first linked account is used.

**Alternatives considered**: Single `account_id` FK on `contacts` (simpler but loses multi-account requirement); multiple `account_id` columns (non-normalised).
