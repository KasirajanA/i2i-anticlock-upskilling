# Tasks: Contact & Account Management (Module 007)

**Input**: Design documents from `specs/007-contact-management/`

**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/api.md ✅ quickstart.md ✅

**Tests**: Not included — not requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks in same phase)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths included in every description

## Path Conventions

- Backend: `backend/app/`, `backend/alembic/`
- Frontend: `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database schema migration — must land before any story code can run.

- [X] T001 Create Alembic migration 007_contact_management.py: CREATE TABLE contacts (id PK, first_name, last_name, email UNIQUE NOT NULL, phone, job_title, primary_account_id FK→accounts NULLABLE, owner_id FK→users NULLABLE, tags JSON default [], created_by_id FK→users, created_at, updated_at, deleted_at; indexes on email UNIQUE, primary_account_id, owner_id, deleted_at); contact_accounts (contact_id FK, account_id FK, linked_at; PK(contact_id, account_id)); accounts (id PK, name, industry, company_size, website, billing_address, owner_id FK NULLABLE, created_by_id FK, created_at, updated_at, deleted_at; indexes on name, owner_id, deleted_at); leads (id PK, first_name, last_name, email, company_name, status default 'new', disqualify_reason, notes, owner_id FK, converted_contact_id FK→contacts NULLABLE, created_at, updated_at, deleted_at; composite index on status+owner_id, index on email); segments (id PK, name, entity_type, filter_spec JSON, owner_id FK, created_at, updated_at; index on owner_id+entity_type); activity_log (id PK, entity_type, entity_id, event_type, actor_id FK NULLABLE, metadata JSON, created_at; index on entity_type+entity_id+created_at); custom_field_definitions (id PK, entity_type, field_key UNIQUE NOT NULL, label, field_type, options JSON NULLABLE, required BOOLEAN default False, created_by_id FK, created_at); custom_field_values (id PK, definition_id FK, entity_type, entity_id, field_value TEXT NULLABLE; UNIQUE index on definition_id+entity_type+entity_id, index on entity_type+entity_id) in backend/alembic/versions/007_contact_management.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: ORM models, Pydantic schemas, TypeScript types, and three shared services (FilterQueryBuilder, ActivityLogger, CustomFieldService) that all user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 [P] Create all 8 SQLAlchemy ORM models: Contact, ContactAccount, Account, Lead, Segment, ActivityLog, CustomFieldDefinition, CustomFieldValue with all column types, FK relationships (Contact.primary_account_id → Account, Lead.converted_contact_id → Contact, etc.), table-level UniqueConstraints, and Index declarations matching data-model.md in backend/app/models/contact.py
- [X] T003 [P] Define all Pydantic v2 schemas: ContactResponse, ContactDetailResponse (includes accounts list and custom_fields list), CreateContactRequest (first_name, last_name, email, phone optional, job_title optional, account_ids list, primary_account_id optional, tags list), UpdateContactRequest, DuplicateWarning (existing_id, existing_email, message), ContactCreateResult (contact optional, duplicate_warning optional), AccountResponse, AccountDetailResponse, CreateAccountRequest, UpdateAccountRequest, TimelineItem (type, id, label, created_at), LeadResponse, CreateLeadRequest (first_name, last_name, email, company_name, notes, owner_id), UpdateLeadRequest (status, disqualify_reason optional), ConvertLeadRequest (create_account bool, create_deal bool, deal_title optional, deal_value optional), ConversionResult (contact_id, account_id optional, deal_id optional, lead_id, status), SegmentRequest (name, entity_type, filter_spec with conditions list), SegmentResponse (id, name, entity_type, live_count, created_at), ImportResultResponse (imported, skipped, errors, error_details list) in backend/app/schemas/contact.py
- [X] T004 [P] Define TypeScript types: Contact interface (id, first_name, last_name, email, phone?, job_title?, primary_account summary?, tags, owner summary?, created_at), ContactDetail interface (adds accounts array with is_archived flag, custom_fields array), Account interface, AccountDetail interface (adds contact_count, timeline_count), Lead interface with LeadStatus enum (new | contacted | qualified | converted | disqualified), Segment interface (id, name, entity_type, live_count, filter_spec), TimelineItem interface (type, id, label, created_at), ImportResult, DuplicateWarning, ContactFilters, AccountFilters, LeadFilters in frontend/src/types/contact.ts
- [X] T005 [P] Create contactApi.ts Axios service module: configure baseURL from VITE_API_BASE_URL env var, enable withCredentials for crm_session cookie, export typed Axios instance; add empty typed stub function exports for all contact, account, lead, and segment endpoints so the module is importable immediately in frontend/src/services/contactApi.ts
- [X] T006 [P] Implement FilterQueryBuilder class: FIELD_MAP dict mapping field keys (name → SQLAlchemy CONCAT(Contact.first_name, ' ', Contact.last_name) expression, email → Contact.email, tag → Contact.tags JSON contains, account_id → ContactAccount.account_id, custom_field_key → CustomFieldValue subquery); OPERATOR_MAP dict mapping operators (eq → ==, contains → ilike with %, in → in_); add(field, operator, value) → self; build(base_query: Select) → Select (chains all conditions with .where()); validate_spec(filter_spec) raises HTTP 422 if >5 conditions or unknown field in backend/app/services/filter_query_builder.py
- [X] T007 [P] Implement ActivityLogger class with async log(event_type: str, entity_type: str, entity_id: int, actor_id: int | None, metadata: dict | None = None) → None method that inserts an ActivityLog row into the provided AsyncSession; constructor accepts an AsyncSession in backend/app/services/activity_logger.py
- [X] T008 [P] Implement CustomFieldService: create_definition(entity_type, field_key, label, field_type, options, required, created_by_id) → CustomFieldDefinition (validates field_key is snake_case 3–50 chars, unique per entity_type; options required when field_type=select); list_definitions(entity_type) → list[CustomFieldDefinition]; get_values(entity_type, entity_id) → list[{key, label, value}] (joins definitions + values, coerces value by field_type); set_value(definition_id, entity_type, entity_id, raw_value) → CustomFieldValue (validates value against field_type: number → float(), date → ISO8601, boolean → "true"/"false", select → in options) in backend/app/services/custom_field_service.py
- [X] T009 [P] Implement GET /api/v1/custom-fields?entity_type= (list definitions, all authenticated users) and POST /api/v1/custom-fields (create definition, Admin only via require_module_access) endpoints using CustomFieldService; register custom_fields router with prefix=/api/v1 in backend/app/main.py in backend/app/api/v1/custom_fields.py

**Checkpoint**: Foundation ready — all four user stories can now begin.

---

## Phase 3: User Story 1 — Create & Manage a Contact (Priority: P1) 🎯 MVP

**Goal**: Sales Rep creates a contact, links it to an account, duplicate detection warns on same email, search and edit work, CSV bulk import available.

**Independent Test**: Create contact `jane@acme.com`, search for "jane", open record, edit phone, archive — all changes persist; attempt to create a second `jane@acme.com` and confirm duplicate_warning in response.

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement sqlite_contact_repository: async create(contact_data, account_ids) → Contact (inserts Contact row + ContactAccount rows in same session), get_by_id(id, include_archived=False) → ContactDetail, list(q, account_id, tag, owner_id, include_archived, cursor, limit) → PaginatedResult (q uses ILIKE on first_name, last_name, email; tag uses JSON_CONTAINS; cursor-based pagination via id), find_by_email(email) → Contact | None (case-insensitive WHERE LOWER(email)=LOWER(:email)), update(id, fields) → Contact, archive(id) → None (sets deleted_at=NOW), link_account(contact_id, account_id) → None, unlink_account(contact_id, account_id) → None in backend/app/repositories/sqlite_contact_repository.py
- [X] T011 [US1] Implement ContactService: create(data, actor) → ContactCreateResult (call find_by_email; if found return ContactCreateResult(duplicate_warning=DuplicateWarning(existing_id, existing_email)); else repo.create + ActivityLogger.log("created", "contact", id, actor.id)), get(id) → ContactDetail (includes custom fields via CustomFieldService.get_values), list(filters) → PaginatedContacts (delegates to repo.list; q filter passes through), update(id, data, actor) → Contact (repo.update + ActivityLogger.log("updated", "contact", id, actor.id, metadata={"changed_fields": [...]})), archive(id, actor) → None (repo.archive + ActivityLogger.log("archived")) in backend/app/services/contact_service.py
- [X] T012 [P] [US1] Implement CSVImporter: accepts UploadFile + duplicate_mode ("skip" | "overwrite"); streams file bytes through csv.DictReader; validates each row (email required + valid format via email-validator or re; first_name, last_name required); in skip mode skip rows whose email exists via find_by_email; in overwrite mode call repo.update for existing; batch-insert new rows in groups of 100 using SQLAlchemy core insert(); accumulate imported/skipped/errors counts; collect error_details [{row, reason}]; return ImportResultResponse in backend/app/services/csv_importer.py
- [X] T013 [P] [US1] Implement all contact API endpoints: GET /api/v1/contacts (list; all roles read; q/account_id/tag/owner_id/include_archived/cursor/limit query params), POST /api/v1/contacts (create; require_module_access("contact_management", write=True); returns 201 ContactDetailResponse or 200 ContactCreateResult with duplicate_warning), GET /api/v1/contacts/{id} (single; all roles), PATCH /api/v1/contacts/{id} (update; Sales Rep own or Admin write guard), DELETE /api/v1/contacts/{id} (archive; Admin only), POST /api/v1/contacts/import (CSV upload; multipart/form-data; file + duplicate_mode fields; Sales Rep/Admin; delegates to CSVImporter) in backend/app/api/v1/contacts.py
- [X] T014 [US1] Register contacts router with prefix=/api/v1 and tags=["contacts"] in backend/app/main.py (alongside custom_fields router registered in T009)
- [X] T015 [P] [US1] Add list_contacts(params: ContactFilters), get_contact(id), create_contact(body), update_contact(id, body), archive_contact(id), import_contacts(file: File, duplicate_mode: string) typed Axios functions that call the correct endpoints with proper request shapes in frontend/src/services/contactApi.ts
- [X] T016 [P] [US1] Create useContacts TanStack Query hook: useContactList(filters: ContactFilters) using useInfiniteQuery with queryKey ["contacts", filters], queryFn calling list_contacts with cursor pageParam, getNextPageParam returning next_cursor, staleTime 30_000; useContact(id) using useQuery; useCreateContact, useUpdateContact, useArchiveContact mutations that invalidate ["contacts"] on settle in frontend/src/hooks/useContacts.ts
- [X] T017 [P] [US1] Implement DuplicateWarningBanner: MUI Alert severity="warning" shown when ContactCreateResult.duplicate_warning is present; displays message text and MUI Link "View existing contact" navigating to /contacts/{existing_id}; dismissible via onClose in frontend/src/components/contacts/DuplicateWarningBanner.tsx
- [X] T018 [P] [US1] Implement ContactForm: MUI form fields for first_name (required), last_name (required), email (required; onBlur triggers GET /api/v1/contacts?email= to surface DuplicateWarningBanner), phone, job_title, tags MUI Autocomplete (freeSolo, chips), account_ids MUI Autocomplete multi-select backed by GET /api/v1/accounts; inline MUI FormHelperText errors from Pydantic validation; DuplicateWarningBanner rendered below email field; onSubmit calls useCreateContact or useUpdateContact in frontend/src/components/contacts/ContactForm.tsx
- [X] T019 [P] [US1] Implement ContactRow MUI TableRow: full name as MUI Link to /contacts/:id, email, primary account name (appended with " (archived)" in italic MUI Typography when account.is_archived), up to 3 tags as MUI Chips with "+N more" overflow, owner display_name, archive MUI IconButton (admin only) in frontend/src/components/contacts/ContactRow.tsx
- [X] T020 [P] [US1] Implement CSVImportDialog: MUI Dialog with MUI Button "Choose CSV file" opening hidden file input, duplicate_mode MUI RadioGroup (skip label "Skip duplicates (default)", overwrite label "Overwrite existing"), upload MUI Button calling import_contacts; MUI LinearProgress during upload; on completion render result table (Imported N / Skipped N / Errors N) with MUI Accordion showing error_details rows; close button in frontend/src/components/contacts/CSVImportDialog.tsx
- [X] T021 [US1] Implement ContactListPage: MUI Paper with search MUI TextField (debounced 300 ms, sets q filter), MUI DataGrid/Table backed by useContactList (virtual infinite scroll via fetchNextPage on scroll), ContactRow per row, "New Contact" MUI Button opening MUI Drawer containing ContactForm, "Import" MUI Button opening CSVImportDialog, role-based visibility of "New Contact" and "Import" (hidden for Support Agent) in frontend/src/pages/ContactListPage.tsx
- [X] T022 [US1] Implement ContactDetailPage: MUI Card header (full name, email, job title), linked accounts MUI Chips (each chip shows account name + "(archived)" badge if archived), phone, tags chips, custom fields MUI Table section (label + value), activity log MUI Timeline (fetched from GET /api/v1/contacts/{id} and activity endpoint), edit MUI Button opening ContactForm in MUI Drawer, archive MUI Button (admin only) with MUI Dialog confirm in frontend/src/pages/ContactDetailPage.tsx
- [X] T023 [US1] Add /contacts route (all authenticated users, RequireAuth) and /contacts/:id route to React Router; protect write-UI components inside pages with role check rather than route guard (Support Agent can view but not write) in frontend/src/App.tsx

**Checkpoint**: User Story 1 independently testable — run quickstart.md Scenarios 1–3 and 6 (CSV import) to validate.

---

## Phase 4: User Story 2 — Manage Company Accounts (Priority: P1)

**Goal**: Users create company accounts, link multiple contacts, and view a unified timeline of all linked contacts, deals, contracts, and tickets.

**Independent Test**: Create account "Acme Corp", link two contacts, open account detail, confirm AccountTimeline shows both contacts; archive the account and confirm linked contacts remain active with "(archived)" indicator.

### Implementation for User Story 2

- [X] T024 [P] [US2] Implement sqlite_account_repository: async create(data) → Account, get_by_id(id, include_archived=False) → Account, list(q, industry, owner_id, include_archived, cursor, limit) → PaginatedResult (q uses ILIKE on name), update(id, fields) → Account, archive(id) → None (sets deleted_at; does NOT cascade to contacts per FR-011), get_contact_count(id) → int in backend/app/repositories/sqlite_account_repository.py
- [X] T025 [US2] Implement AccountService: create(data, actor) → Account (repo.create + ActivityLogger.log("created", "account")), get(id) → AccountDetail (includes contact_count via repo.get_contact_count), list(filters) → PaginatedAccounts, update(id, data, actor) → Account (ActivityLogger.log("updated")), archive(id, actor) → None (repo.archive + ActivityLogger.log("archived"); contacts remain active), get_timeline(account_id) → list[TimelineItem] (asyncio.gather parallel queries: contacts WHERE primary_account_id=id OR contact_accounts.account_id=id; deals WHERE account_id=id stub; tickets WHERE account_id=id stub; merge results into TimelineItem list; sort by created_at desc) in backend/app/services/account_service.py
- [X] T026 [P] [US2] Implement all account endpoints: GET /api/v1/accounts (list; q/industry/owner_id/include_archived/cursor/limit; all roles read), POST /api/v1/accounts (create; Sales Rep/Admin write guard), GET /api/v1/accounts/{id} (single with contact_count), PATCH /api/v1/accounts/{id} (Sales Rep own or Admin), DELETE /api/v1/accounts/{id} (archive; Admin only), GET /api/v1/accounts/{id}/timeline (all roles; calls AccountService.get_timeline) in backend/app/api/v1/accounts.py
- [X] T027 [US2] Register accounts router with prefix=/api/v1 and tags=["accounts"] in backend/app/main.py
- [X] T028 [P] [US2] Add list_accounts(params: AccountFilters), get_account(id), create_account(body), update_account(id, body), archive_account(id), get_account_timeline(id) typed Axios functions to frontend/src/services/contactApi.ts
- [X] T029 [P] [US2] Create useAccounts TanStack Query hook: useAccountList(filters: AccountFilters) with useInfiniteQuery queryKey ["accounts", filters]; useAccount(id) queryKey ["accounts", id]; useAccountTimeline(id) queryKey ["accounts", id, "timeline"]; useCreateAccount, useUpdateAccount, useArchiveAccount mutations invalidating ["accounts"] in frontend/src/hooks/useAccounts.ts
- [X] T030 [P] [US2] Implement AccountTimeline MUI Timeline component: renders list of TimelineItem objects time-sorted; each item shows MUI TimelineDot with type-specific icon (contact=PersonIcon, deal=HandshakeIcon, ticket=SupportAgentIcon), MUI TimelineContent with item.label and formatted date; MUI Skeleton loading state while fetching; "No activity yet" empty state in frontend/src/components/contacts/AccountTimeline.tsx
- [X] T031 [US2] Implement AccountListPage: MUI DataGrid/Table backed by useAccountList with infinite scroll; search MUI TextField (q filter); industry MUI Select filter; archived MUI Switch toggle (include_archived); "New Account" MUI Button opening create form in MUI Drawer; archive action per row (admin only) in frontend/src/pages/AccountListPage.tsx
- [X] T032 [US2] Implement AccountDetailPage: account header (name, industry, company_size badge, website MUI Link, billing_address), linked contacts MUI Table (first_name+last_name, email, MUI Link to /contacts/:id, remove link button for admin), AccountTimeline component below contacts section, edit MUI Button (opens account update form in MUI Drawer), archive MUI Button (admin only) with MUI Dialog confirm in frontend/src/pages/AccountDetailPage.tsx
- [X] T033 [US2] Add /accounts route (all authenticated users, RequireAuth) and /accounts/:id route to React Router in frontend/src/App.tsx

**Checkpoint**: User Story 2 independently testable — run quickstart.md Scenarios 4 and 8 to validate.

---

## Phase 5: User Story 3 — Lead Capture & Qualification (Priority: P2)

**Goal**: Sales Reps create leads, progress them through the New → Contacted → Qualified → Converted/Disqualified lifecycle, and convert a qualified lead into a Contact + Account + Deal atomically.

**Independent Test**: Create lead `prospect@startup.io`, advance status to Qualified, convert with create_account=true and create_deal=true — confirm ConversionResult has contact_id, account_id, deal_id; confirm lead.status=converted and lead.notes appear in the Contact's activity log.

### Implementation for User Story 3

- [X] T034 [P] [US3] Implement sqlite_lead_repository: async create(data) → Lead, get_by_id(id) → Lead, list(status, owner_id, q, cursor, limit) → PaginatedResult (filter by status and/or owner_id; q uses ILIKE on first_name, last_name, email; excludes deleted_at IS NOT NULL by default), update(id, fields) → Lead, archive(id, reason) → Lead (sets deleted_at + disqualify_reason) methods in backend/app/repositories/sqlite_lead_repository.py
- [X] T035 [US3] Implement LeadService: create(data, actor) → Lead (validates actor.role in {admin, sales_rep}; raises HTTP 403 otherwise; repo.create + ActivityLogger.log("created", "lead")), update_status(id, new_status, actor) → Lead (validates lifecycle: allowed forward transitions only {new→contacted, contacted→qualified, qualified→converted, qualified→disqualified, contacted→disqualified}; backward transitions raise HTTP 422 unless actor.role=admin; disqualify_reason required when new_status=disqualified; raises HTTP 409 if lead already converted/disqualified), convert(id, opts: ConvertLeadRequest, actor) → ConversionResult (single async with self._session.begin(): (1) contact_service.create_from_lead → creates Contact from lead fields + copies lead.notes as ActivityLog "converted" entry; (2) if opts.create_account: account_service.create_from_lead → creates Account with lead.company_name; (3) if opts.create_deal: insert stub Deal row with opts.deal_title/deal_value linked to contact and account; (4) repo.update(id, {status: converted, converted_contact_id: contact.id})), disqualify(id, reason, actor) → None (calls update_status + repo.archive) in backend/app/services/lead_service.py
- [X] T036 [P] [US3] Implement all lead endpoints: GET /api/v1/leads (Sales Rep → own leads only; Admin/Manager → all; Support Agent → HTTP 403), POST /api/v1/leads (Sales Rep/Admin only via require_module_access write guard), PATCH /api/v1/leads/{id} (Sales Rep own or Admin), POST /api/v1/leads/{id}/convert (Sales Rep own or Admin; returns 201 ConversionResult) in backend/app/api/v1/leads.py
- [X] T037 [US3] Register leads router with prefix=/api/v1 and tags=["leads"] in backend/app/main.py
- [X] T038 [P] [US3] Add list_leads(params: LeadFilters), get_lead(id), create_lead(body), update_lead(id, body), convert_lead(id, body: ConvertLeadRequest) typed Axios functions to frontend/src/services/contactApi.ts
- [X] T039 [P] [US3] Create useLeads TanStack Query hook: useLeadList(filters: LeadFilters) with useInfiniteQuery queryKey ["leads", filters]; useLead(id) queryKey ["leads", id]; useCreateLead, useUpdateLead, useConvertLead mutations (useConvertLead on success navigates to /contacts/:contact_id) in frontend/src/hooks/useLeads.ts
- [X] T040 [P] [US3] Implement LeadStatusChip MUI Chip with status-to-colour mapping: new→default, contacted→info, qualified→warning, converted→success, disqualified→error; size="small" variant="filled" in frontend/src/components/contacts/LeadStatusChip.tsx
- [X] T041 [P] [US3] Implement LeadConvertDialog: MUI Dialog with "Create Account" MUI FormControlLabel Checkbox (default true), "Create Deal" MUI FormControlLabel Checkbox; when create_deal checked show deal_title MUI TextField (required) and deal_value MUI TextField (number); "Convert Lead" MUI Button calls useConvertLead mutation; on success displays ConversionResult summary (Contact ID, Account ID, Deal ID) with "View Contact" MUI Button; on error shows MUI Alert with error message in frontend/src/components/contacts/LeadConvertDialog.tsx
- [X] T042 [US3] Implement LeadListPage: MUI DataGrid/Table backed by useLeadList; status filter MUI ToggleButtonGroup; owner filter MUI Select; "New Lead" MUI Button opening lead create MUI Drawer form (first_name, last_name, email, company_name, notes TextArea); LeadStatusChip per row; "Convert" MUI Button per row (enabled only when status=qualified) opening LeadConvertDialog; "Disqualify" MUI Button opening reason input MUI Dialog in frontend/src/pages/LeadListPage.tsx
- [X] T043 [US3] Implement LeadDetailPage: lead info (name, email, company_name), LeadStatusChip for current status, status progression MUI Stepper (New → Contacted → Qualified → Converted/Disqualified) with active step, notes MUI TextField (editable for owner/admin), disqualify_reason display when status=disqualified, "Convert Lead" MUI Button (visible when status=qualified) opening LeadConvertDialog, converted_contact_id MUI Link to /contacts/:id when converted in frontend/src/pages/LeadDetailPage.tsx
- [X] T044 [US3] Add /leads and /leads/:id routes; wrap with RequireRole that redirects Support Agent to /access-denied (Sales Rep, Admin, Manager can access; read-only UI for Manager based on role check within page) in frontend/src/App.tsx

**Checkpoint**: User Story 3 independently testable — run quickstart.md Scenario 5 to validate.

---

## Phase 6: User Story 4 — Search, Filter & Segment Contacts (Priority: P2)

**Goal**: Users combine multi-field filters (up to 5 conditions) on the contact list and save the active filter as a named segment; segments show live counts and can be re-applied.

**Independent Test**: Create 10 contacts with varying tags and accounts. Build a filter (tag=enterprise AND account_id=5), verify only matching contacts shown (≤1 s). Save as "Enterprise Contacts" segment, confirm it appears with live_count. Add one more enterprise contact, reload segment, confirm count increments.

### Implementation for User Story 4

- [X] T045 [P] [US4] Implement sqlite_segment_repository: async create(name, entity_type, filter_spec, owner_id) → Segment, list(owner_id, entity_type=None) → list[Segment] (optional entity_type filter), get_by_id(id) → Segment, delete(id) → None methods in backend/app/repositories/sqlite_segment_repository.py
- [X] T046 [US4] Implement SegmentService: create(name, entity_type, filter_spec, owner) → SegmentResponse (validate max 5 conditions and each condition.field exists in FilterQueryBuilder.FIELD_MAP; raise HTTP 422 on violation; repo.create + compute live_count via FilterQueryBuilder.build on base SELECT COUNT(*) FROM contacts WHERE deleted_at IS NULL), list(owner, entity_type=None) → list[SegmentResponse] (each with live_count computed via FilterQueryBuilder), get_live_count(segment_id) → int (reload filter_spec, apply FilterQueryBuilder, return COUNT) in backend/app/services/segment_service.py
- [X] T047 [P] [US4] Implement GET /api/v1/segments?entity_type= (list segments for current user with live_count) and POST /api/v1/segments (create; all authenticated users except Support Agent for write) endpoints using SegmentService; include GET /api/v1/segments/{id}/count for live count refresh in backend/app/api/v1/segments.py
- [X] T048 [US4] Register segments router with prefix=/api/v1 and tags=["segments"] in backend/app/main.py
- [X] T049 [P] [US4] Add list_segments(entity_type: string), create_segment(body: SegmentRequest), get_segment_count(id) typed Axios functions to frontend/src/services/contactApi.ts
- [X] T050 [P] [US4] Create useSegments TanStack Query hook: useSegmentList(entity_type: string) with queryKey ["segments", entity_type], staleTime 60_000; useCreateSegment mutation that invalidates ["segments", entity_type] on settle in frontend/src/hooks/useSegments.ts
- [X] T051 [P] [US4] Implement FilterBuilder component: MUI Stack of condition rows; each row has field MUI Select (options: name, email, tag, account_id, industry, custom_field_key), operator MUI Select (eq → "is", contains → "contains", in → "includes"), value MUI TextField or MUI Autocomplete depending on field; "Add filter" MUI Button (disabled when 5 conditions reached); ✕ MUI IconButton to remove each row; onChange callback emits current FilterSpec to parent in frontend/src/components/contacts/FilterBuilder.tsx
- [X] T052 [P] [US4] Implement SegmentPanel component: collapsible MUI Drawer or MUI Accordion showing list of saved segments for entity_type="contact" from useSegmentList; each segment shows name and live_count MUI Chip; "Apply" MUI Button calls parent onApplySegment(filter_spec) callback; "Save active filters as segment" MUI Button opens MUI Dialog asking for segment name then calls useCreateSegment mutation in frontend/src/components/contacts/SegmentPanel.tsx
- [X] T053 [US4] Extend ContactListPage: add FilterBuilder collapsible section below search bar (toggle with "Advanced filters" MUI Button); lift filterSpec state up from FilterBuilder to ContactListPage and merge into useContactList(filters) alongside existing q filter; add "Segments" MUI IconButton opening SegmentPanel; SegmentPanel.onApplySegment sets activeFilters in ContactListPage state which re-feeds FilterBuilder in frontend/src/pages/ContactListPage.tsx

**Checkpoint**: User Story 4 independently testable — run quickstart.md Scenarios 3 and 7 to validate.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Admin custom field creation UI, role guard wiring, linting, and full validation suite.

- [X] T054 [P] Add CustomFieldForm component: admin-only MUI Dialog with label MUI TextField (auto-derives field_key as snake_case slug in real-time), field_type MUI Select (text/number/date/boolean/select), options MUI Chip input (shown only when field_type=select), required MUI Checkbox; "Save" calls POST /api/v1/custom-fields; on success invalidates custom field queries; integrate as "Add Custom Field" MUI Fab button in ContactDetailPage admin section in frontend/src/components/contacts/CustomFieldForm.tsx
- [X] T055 [P] Verify require_module_access("contact_management") dependency is applied to all contacts, accounts, leads, and segments routers per MODULE_PERMISSIONS matrix from Module 006; Support Agent access: read contacts/accounts (no write), no leads access in backend/app/api/v1/ router files
- [X] T056 [P] Run Ruff linter (ruff check backend/app/) and resolve all violations in all new backend/app/ files added in this module
- [X] T057 [P] Run ESLint (npx eslint frontend/src/) and tsc --noEmit and resolve all violations in all new frontend/src/ files added in this module
- [ ] T058 Run quickstart.md Scenarios 1–9 end-to-end against dev servers; verify SC-001 (contact create ≤60 s), SC-002 (search ≤1 s on 100K records — profile query plan), SC-003 (lead conversion ≤2 min), SC-004 (CSV import 1000 rows ≤2 min), SC-005 (duplicate detection on every save); document any failures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — run `alembic upgrade head` before any story code
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)** and **US2 (Phase 4)**: Both depend on Phase 2; these two P1 stories can run in parallel if team is staffed
- **US3 (Phase 5)** and **US4 (Phase 6)**: Depend on Phase 2; US4 extends US1's ContactListPage so benefits from US1 complete
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: No dependency on US2/US3/US4 — independently testable after Phase 2
- **US2 (P1)**: No dependency on US1/US3/US4 — independently testable after Phase 2 (accounts are a separate entity)
- **US3 (P2)**: LeadService.convert calls contact_service.create_from_lead and account_service methods — depends on US1 and US2 being complete before conversion works end-to-end
- **US4 (P2)**: FilterBuilder and SegmentPanel integrate into ContactListPage (T021 from US1) — T053 depends on T021; US4 backend (FilterQueryBuilder in Phase 2) is independent

### Within Each User Story

- Repository → Service → Router (backend layer ordering)
- contactApi.ts → Hooks → Leaf components → Page → Router wiring (frontend layer ordering)
- Each page depends on its child components being available

---

## Parallel Execution Examples

### Phase 2 Parallel Block (all 8 tasks concurrently)

```
T002  ORM models (contact.py)
T003  Pydantic schemas (schemas/contact.py)
T004  TypeScript types (types/contact.ts)
T005  contactApi.ts Axios stub (services/contactApi.ts)
T006  FilterQueryBuilder (services/filter_query_builder.py)
T007  ActivityLogger (services/activity_logger.py)
T008  CustomFieldService (services/custom_field_service.py)
T009  custom_fields router (api/v1/custom_fields.py)
```

### Phase 3 Parallel Block (backend leaf + frontend leaf tasks)

```
T010  sqlite_contact_repository (repositories/sqlite_contact_repository.py)
T012  CSVImporter (services/csv_importer.py)
T013  contacts.py router (api/v1/contacts.py)
T015  contactApi.ts contact functions
T016  useContacts hook
T017  DuplicateWarningBanner component
T018  ContactForm component
T019  ContactRow component
T020  CSVImportDialog component
```

Nine tasks in parallel across nine different files — then T011, T014, T021, T022, T023 sequentially.

### Phase 5 Parallel Block

```
T034  sqlite_lead_repository
T036  leads.py router
T038  contactApi.ts lead functions
T039  useLeads hook
T040  LeadStatusChip component
T041  LeadConvertDialog component
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002–T009) — critical blocking phase
3. Complete Phase 3: User Story 1 — contacts (T010–T023)
4. Complete Phase 4: User Story 2 — accounts (T024–T033)
5. **STOP and VALIDATE**: quickstart.md Scenarios 1–4, 6, 8–9
6. Deploy/demo — full contact and account management with CSV import, duplicate detection, unified timeline

### Incremental Delivery

1. Phase 1 + 2 → Infrastructure ready
2. US1 complete → Contacts with search, duplicate detection, CSV import (MVP core)
3. US2 complete → Accounts with unified timeline
4. US3 complete → Lead pipeline with atomic conversion
5. US4 complete → Saved segments with live counts
6. Polish → Full role matrix validation; custom field admin UI

### Parallel Team Strategy

After Phase 2 completes:
- **Dev A**: User Story 1 (T010–T023)
- **Dev B**: User Story 2 (T024–T033)
- **Dev C**: User Story 3 (T034–T044) — can start LeadService stub in parallel
- **Dev D** (if available): User Story 4 backend (T045–T048) — SegmentService builds on FilterQueryBuilder

---

## Notes

- [P] = different file from all other [P] tasks in the same phase; safe to run concurrently
- [US1/US2/US3/US4] = maps task to user story for traceability and independent delivery
- T001 (Alembic migration) must run `alembic upgrade head` before any integration testing
- T025 (AccountService.get_timeline) references deals and tickets tables that belong to later modules — implement as `asyncio.gather` returning empty lists for deal/ticket items until those modules exist; the contacts query is live immediately
- T035 (LeadService.convert) creates a "Deal stub" — since the Sales Pipeline module (not yet built) owns the deals table, use a placeholder that logs a "deal stub created" ActivityLog entry and returns a synthetic deal_id until Module 008 wires up the real DealService
- T006 (FilterQueryBuilder) uses SQLAlchemy column expressions from contact.py — ensure T002 is committed before running FilterQueryBuilder tests
- CSV import (T012) uses stdlib `csv` module only — no additional pip packages needed
- storage/ directory changes are not needed for this module (no file uploads beyond CSV, which is streamed through memory)
