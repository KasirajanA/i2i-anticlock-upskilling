# Implementation Plan: Contact & Account Management

**Branch**: `007-contact-management` | **Date**: 2026-06-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-contact-management/spec.md`

---

## Summary

Build the foundational CRM contact and account system: contacts (with email-based duplicate detection and custom fields), company accounts (with unified multi-module timeline), lead capture with lifecycle management and atomic Lead → Contact + Account + Deal conversion, bulk CSV import (skip/overwrite modes), saved named segments, and role-scoped access (Support Agents read-only; Sales Reps own-data write; Admin full access). Backend: Python 3.14 + FastAPI (async) + SQLAlchemy 2.x/aiosqlite. Frontend: React 18 + TypeScript + MUI v6.

---

## Technical Context

**Language/Version**: Python 3.14 (backend), TypeScript 5.x / Node 20+

**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy 2.x, aiosqlite, Pydantic v2, `csv` (stdlib)
- Frontend: React 18, MUI v6, TanStack Query v5, Vite, Vitest, React Testing Library

**Storage**: SQLite via SQLAlchemy 2.x — new tables: `contacts`, `contact_accounts`, `accounts`, `leads`, `segments`, `activity_log`, `custom_field_definitions`, `custom_field_values`

**Testing**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend)

**Target Platform**: Linux server (backend), modern browsers Chrome 120+, Firefox 121+, Safari 17+

**Project Type**: Web application — async REST API + React SPA

**Performance Goals**:
- SC-001: Contact create + link ≤ 60 s (UI flow)
- SC-002: Contact search returns ≤ 1 s for 100,000 records
- SC-003: Lead conversion ≤ 2 min (single screen)
- SC-004: Bulk CSV import of 1,000 contacts ≤ 2 min
- SC-005: Duplicate detection on every save, zero false negatives for exact email

**Constraints**:
- No hard-delete (soft-archive only)
- Custom fields defined globally by Admin (not per-user)
- CSV import limited to CSV format; API-based import out of scope
- Lead conversion is atomic (single transaction)
- Multi-account contacts (many-to-many)

**Scale/Scope**: Up to 100,000 contacts; ≤ 1,000 accounts; ≤ 5 filter conditions per segment; ≤ 50 custom fields per entity type

---

## Constitution Check

### Pre-Design Gate

| Principle | Status | Evidence |
|-----------|--------|---------|
| I. Coding Standards | ✅ PASS | PEP 8 + Ruff; TypeScript strict; ESLint Airbnb |
| II. SOLID | ✅ PASS | `ContactService`, `AccountService`, `LeadService`, `CSVImporter`, `FilterQueryBuilder`, `CustomFieldService` — each single-responsibility; `IContactRepository` abstraction |
| III. DRY | ✅ PASS | Duplicate-check logic once in `ContactService._check_duplicate()`; `FilterQueryBuilder` used by both ad-hoc search and segment evaluation |
| IV. Security First | ✅ PASS | Email normalisation to lowercase on write; parameterised queries; role guard on write endpoints; MIME + size check on CSV file upload |
| V. UX | ✅ PASS | Duplicate warning non-blocking with link to existing record; inline validation on required fields; CSV import shows progress and result summary; archived account labelled `(archived)` |

**Constitution Check: PASS — proceed to Phase 1.**

### Post-Design Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| II. SOLID — O/C | ✅ PASS | New filter fields added to `FilterQueryBuilder` without modifying `ContactService` |
| III. DRY | ✅ PASS | Soft-delete filter applied once in `BaseContactQuery._apply_archive_filter()` |
| IV. Security | ✅ PASS | Support Agent write-access blocked at route dependency level; no raw SQL string interpolation |

---

## Project Structure

### Documentation (this feature)

```text
specs/007-contact-management/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── api.md           ← Phase 1 output
└── tasks.md             ← Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   └── contact.py                  # ORM: Contact, ContactAccount, Account, Lead, Segment,
│   │                                   #       ActivityLog, CustomFieldDefinition, CustomFieldValue
│   ├── schemas/
│   │   └── contact.py                  # Pydantic v2: ContactResponse, AccountResponse, LeadResponse,
│   │                                   #              SegmentRequest, ImportResultResponse
│   ├── repositories/
│   │   ├── sqlite_contact_repository.py
│   │   ├── sqlite_account_repository.py
│   │   └── sqlite_lead_repository.py
│   ├── services/
│   │   ├── contact_service.py          # CRUD, duplicate check, archive
│   │   ├── account_service.py          # CRUD, archive, timeline aggregation
│   │   ├── lead_service.py             # Lifecycle, atomic conversion
│   │   ├── csv_importer.py             # Streaming CSV parse, batch upsert, skip/overwrite
│   │   ├── filter_query_builder.py     # Filter-to-SQL builder (shared by search + segments)
│   │   └── custom_field_service.py     # Definition CRUD, typed value get/set
│   └── api/
│       └── v1/
│           ├── contacts.py             # CRUD + import + search endpoints
│           ├── accounts.py             # CRUD + timeline endpoint
│           ├── leads.py                # CRUD + convert endpoint
│           ├── segments.py             # CRUD + live-count endpoint
│           └── custom_fields.py        # Admin: define custom fields
└── tests/
    ├── unit/
    │   ├── test_contact_service.py
    │   ├── test_lead_service.py
    │   ├── test_csv_importer.py
    │   └── test_filter_query_builder.py
    └── integration/
        ├── test_contacts_api.py
        ├── test_accounts_api.py
        ├── test_leads_api.py
        └── test_segments_api.py

frontend/
├── src/
│   ├── types/
│   │   └── contact.ts                  # Contact, Account, Lead, Segment, CustomField, LeadStatus
│   ├── services/
│   │   └── contactApi.ts               # Axios wrappers for all contact/account/lead/segment endpoints
│   ├── hooks/
│   │   ├── useContacts.ts              # TanStack Query: infinite list + detail + mutations
│   │   ├── useAccounts.ts
│   │   └── useLeads.ts
│   ├── components/
│   │   └── contacts/
│   │       ├── ContactRow.tsx          # Single contact row (name, email, account, tags)
│   │       ├── ContactForm.tsx         # Create/edit form with inline validation + duplicate warning
│   │       ├── DuplicateWarningBanner.tsx  # Non-blocking duplicate alert + "View Existing" link
│   │       ├── AccountTimeline.tsx     # Unified timeline list for account detail
│   │       ├── LeadStatusChip.tsx      # MUI Chip coloured by lead status
│   │       ├── LeadConvertDialog.tsx   # Conversion wizard (create Account + Deal options)
│   │       ├── SegmentPanel.tsx        # Saved segments list with live counts
│   │       ├── FilterBuilder.tsx       # Multi-condition filter UI (up to 5 conditions)
│   │       ├── CSVImportDialog.tsx     # Upload + mode select + result summary
│   │       └── CustomFieldForm.tsx     # Admin: define new custom field
│   └── pages/
│       ├── ContactListPage.tsx
│       ├── ContactDetailPage.tsx
│       ├── AccountListPage.tsx
│       ├── AccountDetailPage.tsx
│       ├── LeadListPage.tsx
│       └── LeadDetailPage.tsx
└── tests/
    ├── ContactListPage.test.tsx
    ├── ContactCreateForm.test.tsx
    ├── LeadConvertDialog.test.tsx
    └── AccountTimeline.test.tsx
```

**Structure Decision**: Web application (Option 2) — consistent across all CRM modules.

---

## Key Design Decisions

### Duplicate Detection (transactional)

```python
class ContactService:
    async def create(self, data: CreateContactRequest, actor: User) -> ContactCreateResult:
        async with self._session.begin():
            existing = await self._repo.find_by_email(data.email)
            if existing:
                return ContactCreateResult(duplicate_warning=DuplicateInfo(existing_id=existing.id))
            contact = Contact(**data.model_dump())
            self._session.add(contact)
            await self._session.flush()
            await self._activity_logger.log("created", contact, actor)
        return ContactCreateResult(contact=contact)
```

### Atomic Lead Conversion

```python
class LeadService:
    async def convert(self, lead_id: int, opts: ConvertOptions, actor: User) -> ConversionResult:
        async with self._session.begin():
            lead = await self._repo.get(lead_id)
            contact = await self._contact_service.create_from_lead(lead, session=self._session)
            account = await self._account_service.create_from_lead(lead, session=self._session) if opts.create_account else None
            deal = await self._deal_service.create_from_lead(lead, contact, account, opts, session=self._session) if opts.create_deal else None
            lead.status = LeadStatus.CONVERTED
            lead.converted_contact_id = contact.id
            await self._activity_logger.log("converted", lead, actor, metadata={"contact_id": contact.id})
        return ConversionResult(contact_id=contact.id, account_id=account.id if account else None, deal_id=deal.id if deal else None)
```

### Filter Query Builder (shared by search + segments)

```python
class FilterQueryBuilder:
    def __init__(self):
        self._conditions: list[ColumnElement] = []

    def add(self, field: str, operator: str, value: Any) -> "FilterQueryBuilder":
        col = FIELD_MAP[field]  # maps field key to ORM column
        self._conditions.append(OPERATOR_MAP[operator](col, value))
        return self

    def build(self, base_query: Select) -> Select:
        for cond in self._conditions:
            base_query = base_query.where(cond)
        return base_query
```

### React Infinite Contact List

```typescript
const useContacts = (filters: ContactFilters) =>
  useInfiniteQuery({
    queryKey: ['contacts', filters],
    queryFn: ({ pageParam }) => contactApi.list({ ...filters, cursor: pageParam }),
    getNextPageParam: (page) => page.next_cursor,
    staleTime: 30_000,
  });
```

---

## Complexity Tracking

> No constitution violations — table left empty intentionally.
