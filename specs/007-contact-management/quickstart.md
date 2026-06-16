# Quickstart Validation Guide: Contact & Account Management (Module 007)

**Prerequisites**: Backend running on `http://localhost:8000`, frontend on `http://localhost:5173`. Modules 005 (Auth) and 006 (User Mgmt) operational. At least one Sales Rep and one Admin user exist.

---

## Setup

```bash
cd backend && python -m uvicorn app.main:app --reload
cd frontend && npm run dev

# Run tests
cd backend && pytest tests/contacts/ tests/accounts/ tests/leads/ -v
cd frontend && npm test -- --testPathPattern="(contact|account|lead)"
```

---

## Scenario 1 — Create a Contact (FR-001, SC-001)

1. Log in as Sales Rep.
2. Navigate to **Contacts → New Contact**.
3. Enter: First name `Jane`, Last name `Doe`, Email `jane@acme.com`, Job title `VP Engineering`, link to account `Acme Corp`.
4. Submit.

**Expected**:
- Contact appears in list immediately.
- Activity log entry `created` added.
- Total time from form open to saved: ≤ 60 s.
- `GET /api/v1/contacts/1` returns full record with linked account.

---

## Scenario 2 — Duplicate Email Warning (FR-003, SC-005)

1. Create a second contact with email `jane@acme.com` (same as above).

**Expected**:
- A warning banner appears: `"A contact with this email already exists."` with a link to the existing contact.
- Warning does not block the form; user can still save if they choose.
- After warning appears, clicking **View Existing** navigates to the original contact.

---

## Scenario 3 — Contact Search (FR-007, SC-002)

1. Navigate to the **Contacts** list.
2. Type `jane` in the search bar.

**Expected**:
- Results appear in ≤ 1 s.
- All contacts with "jane" in name or email returned.

3. Apply tag filter `enterprise`.
   - **Expected**: Only contacts tagged `enterprise` shown.

---

## Scenario 4 — Account Unified Timeline (FR-004)

1. Create an account `Acme Corp`.
2. Link two contacts, create a deal, and open a support ticket — all referencing `Acme Corp`.
3. Navigate to the account's detail view.

**Expected**:
- Unified timeline shows all linked contacts, the deal, and the ticket in chronological order.
- Each item has the correct type label and timestamp.

---

## Scenario 5 — Lead Lifecycle & Conversion (FR-005, FR-006, SC-003)

1. Log in as Sales Rep. Navigate to **Leads → New Lead**.
2. Enter: `prospect@startup.io`, company `StartupCo`, status `New`.
3. Change status to `Contacted`, then `Qualified`.
4. Click **Convert Lead**.
5. In the conversion dialog: check `Create Account` and `Create Deal` with deal title `StartupCo Q3`.

**Expected**:
- HTTP 201: `contact_id`, `account_id`, `deal_id` all populated.
- Lead `status` becomes `converted`; Lead record links to new contact.
- Lead notes are visible in the new Contact's activity log.
- Conversion completes in a single screen interaction in ≤ 2 min.

---

## Scenario 6 — Bulk CSV Import (FR-008, SC-004)

1. Prepare a CSV with 1,000 contacts (use `scripts/generate_test_contacts.py`).
2. Navigate to **Contacts → Import**.
3. Select `skip` duplicate mode. Upload the file.

**Expected**:
- Import completes in ≤ 2 minutes.
- Result summary shows `imported: N`, `skipped: M`, `errors: 0`.
- Invalid rows (bad email) listed in `error_details`.

4. Import same file again with `overwrite` mode.
   - **Expected**: Existing contacts updated with CSV values; no new duplicates created.

---

## Scenario 7 — Saved Segment (FR-007)

1. Apply filter: tag = `enterprise`.
2. Click **Save as Segment**. Name it `Enterprise Contacts`.

**Expected**:
- Segment appears in the **Segments** panel with live count.
- After adding a new enterprise-tagged contact, the count updates on next segment load.

---

## Scenario 8 — Archived Account Indicator (FR-011)

1. Archive account `Acme Corp`.
2. View the contacts linked to `Acme Corp`.

**Expected**:
- `Acme Corp` displayed with `(archived)` indicator on each linked contact record.
- Contacts themselves remain active and accessible.
- `Acme Corp` does not appear in active account search by default (`include_archived=false`).

---

## Scenario 9 — Role Access Control

1. Log in as Support Agent. Navigate to **Contacts**.
   - **Expected**: Contacts visible in read-only mode; **New Contact** button absent.
2. Attempt `POST /api/v1/contacts` as Support Agent.
   - **Expected**: HTTP 403.
3. Navigate to **Leads** as Support Agent.
   - **Expected**: Redirect to `/access-denied`.

---

## Unit Test Checklist

| Test File | Coverage |
|-----------|----------|
| `tests/unit/test_contact_service.py` | Create, duplicate detection, archive, custom fields |
| `tests/unit/test_lead_service.py` | Status transitions, conversion atomicity, notes preservation |
| `tests/unit/test_csv_importer.py` | Skip vs overwrite modes, error detection, row streaming |
| `tests/unit/test_filter_query_builder.py` | Segment filter-to-SQL, max 5 conditions |
| `tests/integration/test_contacts_api.py` | CRUD, search, duplicate warning, archive |
| `tests/integration/test_accounts_api.py` | CRUD, timeline endpoint, archived indicator |
| `tests/integration/test_leads_api.py` | Lifecycle, conversion endpoint, role access |
| `tests/integration/test_segments_api.py` | Create, live count, filter execution |
| `frontend/tests/ContactListPage.test.tsx` | Search, filter, pagination |
| `frontend/tests/ContactCreateForm.test.tsx` | Duplicate warning, inline validation |
| `frontend/tests/LeadConvertDialog.test.tsx` | Conversion form, success state |
| `frontend/tests/AccountTimeline.test.tsx` | Unified timeline rendering |
