# Implementation Plan: Customer Support

**Branch**: `003-customer-support` | **Date**: 2026-06-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-customer-support/spec.md`

---

## Summary

Build a full-lifecycle support ticket system for the CRM: agents create tickets (auto-ID `I2I-CRM-NNNN`), progress them through Open → In Progress → Resolved → Closed, add replies and internal notes, and the system enforces SLA targets per priority with badge flagging and Admin in-app alerts. Backend: Python 3.14 + FastAPI (async) + SQLite via SQLAlchemy 2.x/aiosqlite + APScheduler 4.x. Frontend: React 18 + TypeScript + MUI v6.

---

## Technical Context

**Language/Version**: Python 3.14 (backend), TypeScript 5.x / Node 20+ (frontend)

**Primary Dependencies**:
- Backend: FastAPI, Uvicorn, SQLAlchemy 2.x, aiosqlite, APScheduler 4.x, Pydantic v2
- Frontend: React 18, MUI v6, TanStack Query v5, Vite, Vitest, React Testing Library

**Storage**: SQLite (MVP) via SQLAlchemy 2.x async engine (`sqlite+aiosqlite://`)

**Testing**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend)

**Target Platform**: Linux server (backend), modern browsers — Chrome 120+, Firefox 121+, Safari 17+

**Project Type**: Web application — async REST API + React SPA

**Performance Goals**:
- SC-001: Ticket creation < 60 seconds end-to-end (UI flow)
- SC-002: SLA breach flag within 5 minutes of deadline (scheduler poll interval)
- SC-003: Ticket queue loads ≤ 2 s for up to 1,000 open tickets (cursor pagination)
- SC-004: Auto-reopen within 1 minute of customer reply

**Constraints**:
- No Redis, no Celery — SQLite-only for MVP
- Business hours not factored into SLA (24/7 timers)
- No email-to-ticket ingestion in v1 (replies entered manually)
- In-app notifications via Module 008 `NotificationService`

**Scale/Scope**: ≤ 1,000 open tickets; 4 priority levels; 5-minute SLA scheduler interval

---

## Constitution Check

### Pre-Design Gate

| Principle | Status | Evidence |
|-----------|--------|---------|
| I. Coding Standards | ✅ PASS | PEP 8 + Ruff enforced; TypeScript strict mode; ESLint Airbnb |
| II. SOLID | ✅ PASS | `TicketService`, `SLAEngine`, `TicketRepository`, `ActivityLogger` — each single-responsibility; `ITicketRepository` abstraction; status machine open for extension |
| III. DRY | ✅ PASS | Shared `TicketStatus`/`TicketPriority` enums backend+frontend; single `TicketRow` React component reused in `MyQueue`, `UnassignedQueue`, `AllTickets` |
| IV. Security First | ✅ PASS | Pydantic v2 request validation; role guard on all endpoints; status-transition enforcement server-side; no plaintext secrets |
| V. UX | ✅ PASS | SLA badge with `aria-label`; MUI `Chip` colour coding per priority; inline form validation; destructive Close action requires confirmation |

**Constitution Check: PASS — proceed to Phase 1.**

### Post-Design Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| II. SOLID — O/C | ✅ PASS | New SLA policy levels added to config dict without modifying `SLAEngine` |
| II. SOLID — D | ✅ PASS | `TicketService` depends on `ITicketRepository`; `SLAEngine` receives config via constructor injection |
| III. DRY | ✅ PASS | SLA due-date calculation in `SLAEngine.compute_due_dates()` only |
| IV. Security | ✅ PASS | Agent status-revert blocked at service layer; role check at route layer |

---

## Project Structure

### Documentation (this feature)

```text
specs/003-customer-support/
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
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/
│   │   └── support.py                  # ORM: Ticket, Reply, SLARecord, TicketActivityLog, TicketSequence
│   ├── schemas/
│   │   └── support.py                  # Pydantic v2 request/response schemas
│   ├── repositories/
│   │   ├── base.py                     # ITicketRepository (abstract)
│   │   └── sqlite_ticket_repository.py
│   ├── services/
│   │   ├── ticket_service.py           # Business logic: create, transition, assign, reopen
│   │   ├── sla_engine.py               # SLA due-date computation + breach detection
│   │   └── activity_logger.py          # Append-only activity log writer
│   ├── scheduler/
│   │   └── jobs.py                     # APScheduler: SLA breach poll job (5 min)
│   └── api/
│       └── v1/
│           ├── support_tickets.py      # CRUD + status transition endpoints
│           ├── support_replies.py      # Reply + note endpoints
│           ├── support_activity.py     # Activity log endpoint
│           └── _test.py               # Test-only clock-advance + job-trigger endpoints
└── tests/
    ├── unit/
    │   ├── test_ticket_service.py
    │   ├── test_sla_engine.py
    │   └── test_ticket_id_generator.py
    └── integration/
        ├── test_tickets_api.py
        └── test_replies_api.py

frontend/
├── src/
│   ├── types/
│   │   └── support.ts                  # Shared TS types: Ticket, Reply, SLARecord, enums
│   ├── services/
│   │   └── supportApi.ts               # Axios wrappers for all support endpoints
│   ├── hooks/
│   │   ├── useTickets.ts               # TanStack Query: infinite list + detail
│   │   └── useTicketMutations.ts       # Create, update, assign, reply mutations
│   ├── components/
│   │   └── support/
│   │       ├── TicketRow.tsx           # Single ticket row (reused in all queue views)
│   │       ├── TicketStatusChip.tsx    # MUI Chip coloured by status
│   │       ├── PriorityBadge.tsx       # MUI Chip coloured by priority
│   │       ├── SLAIndicator.tsx        # Countdown + breach/warning icon
│   │       ├── TicketQueue.tsx         # Filterable, paginated ticket list
│   │       ├── TicketDetail.tsx        # Full ticket view with reply thread
│   │       ├── ReplyForm.tsx           # Compose reply or internal note
│   │       └── ActivityTimeline.tsx    # Audit log display
│   └── pages/
│       ├── SupportQueuePage.tsx        # My Tickets / Unassigned / All Tickets tabs
│       ├── TicketDetailPage.tsx        # Full ticket detail
│       └── NewTicketPage.tsx           # Create ticket form
└── tests/
    ├── TicketQueue.test.tsx
    ├── TicketDetail.test.tsx
    ├── SLAIndicator.test.tsx
    └── ReplyForm.test.tsx
```

**Structure Decision**: Web application (Option 2) — separate `backend/` and `frontend/` directories co-located in the monorepo root, consistent with Module 008.

---

## Key Design Decisions

### Ticket ID Generation

```python
class TicketIDGenerator:
    async def next_ref(self, session: AsyncSession) -> tuple[int, str]:
        result = await session.execute(
            update(TicketSequence)
            .values(next_value=TicketSequence.next_value + 1)
            .returning(TicketSequence.next_value)
        )
        seq = result.scalar_one()
        return seq, f"I2I-CRM-{seq:04d}"
```

Single-row `ticket_sequence` table updated atomically inside the ticket creation transaction.

### SLA Engine

```python
class SLAEngine:
    def __init__(self, policy: dict[str, dict]):
        self._policy = policy  # injected, not hard-coded

    def compute_due_dates(self, priority: str, from_dt: datetime) -> tuple[datetime, datetime]:
        p = self._policy[priority]
        return (
            from_dt + timedelta(hours=p["first_response_hours"]),
            from_dt + timedelta(hours=p["resolution_hours"]),
        )

    async def check_breaches(self, session: AsyncSession) -> list[int]:
        """Returns ticket IDs with newly detected breaches; updates sla_records."""
```

### Status State Machine

```python
ALLOWED_TRANSITIONS = {
    "open":        {"in_progress"},           # agent or admin
    "in_progress": {"resolved"},              # agent or admin
    "resolved":    {"closed", "open"},        # "open" = reopen by system only
    "closed":      set(),                     # agent: no transitions; admin: any
}
ADMIN_REVERSIONS = {                          # admin-only reversions
    "in_progress": {"open"},
    "resolved":    {"in_progress", "open"},
    "closed":      {"resolved", "in_progress", "open"},
}
```

### React Queue Architecture

```typescript
// TicketQueue.tsx — reused for My Tickets, Unassigned, All Tickets
interface TicketQueueProps {
  queue: 'mine' | 'unassigned' | 'all';
  filters?: TicketFilters;
}

// useTickets.ts — TanStack Query infinite list
const useTickets = (params: TicketQueryParams) =>
  useInfiniteQuery({
    queryKey: ['tickets', params],
    queryFn: ({ pageParam }) => supportApi.listTickets({ ...params, cursor: pageParam }),
    getNextPageParam: (page) => page.next_cursor,
  });
```

---

## Complexity Tracking

> No constitution violations — table left empty intentionally.
