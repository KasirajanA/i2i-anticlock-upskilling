# Implementation Plan: Notifications & Alerts

**Branch**: `008-notifications` | **Date**: 2026-06-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-notifications/spec.md`

---

## Summary

Deliver an in-app notification system for the CRM: real-time badge + panel driven by Server-Sent Events (SSE), per-user event-type preferences, Admin-configurable organisation-wide rules, bulk-action digest batching, and a scheduled 30-day purge job. Backend: Python 3.14 + FastAPI (async) + SQLite via SQLAlchemy 2.x/aiosqlite + APScheduler 4.x. Frontend: React 18 + TypeScript + MUI v6.

---

## Technical Context

**Language/Version**: Python 3.14 (backend), TypeScript 5.x / Node 20+ (frontend)

**Primary Dependencies**:
- Backend: FastAPI, Uvicorn, SQLAlchemy 2.x, aiosqlite, sse-starlette, APScheduler 4.x, Pydantic v2
- Frontend: React 18, MUI v6, TanStack Query v5, Vite, Vitest, React Testing Library

**Storage**: SQLite (MVP) via SQLAlchemy 2.x async engine (`sqlite+aiosqlite://`)

**Testing**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend)

**Target Platform**: Linux server (backend), modern browsers — Chrome 120+, Firefox 121+, Safari 17+ (frontend)

**Project Type**: Web application — async REST API + React SPA

**Performance Goals**:
- SC-001: Notification badge appears ≤ 5 s after event (SSE push)
- SC-002: Login → pending notifications visible ≤ 2 s
- SC-004: Bulk ≥10 same-user events → single digest (60-s flush window)

**Constraints**:
- No Redis, no Celery — SQLite-only broker for MVP
- No email or push notifications (out of scope v1)
- In-process SSE fan-out (per-client `asyncio.Queue`); horizontal scale deferred

**Scale/Scope**: ≤1,000 concurrent users (SQLite WAL mode + connection pool); 8 event types; ≤100 Admin rules

---

## Constitution Check

### Pre-Design Gate

| Principle | Status | Evidence |
|-----------|--------|---------|
| I. Coding Standards | ✅ PASS | PEP 8 + Ruff enforced; TypeScript strict mode; ESLint Airbnb |
| II. SOLID | ✅ PASS | `NotificationService`, `RuleEngine`, `SSEManager`, `NotificationRepository` — each single-responsibility; `INotificationRepository` abstraction; event registry open for extension |
| III. DRY | ✅ PASS | Shared `EventType` enum backend+frontend; single `NotificationItem` React component used in panel and settings preview |
| IV. Security First | ✅ PASS | Pydantic v2 request validation; auth middleware on all endpoints; `token` query param for SSE validated server-side; no secrets in code |
| V. UX | ✅ PASS | `aria-live="polite"` region; MUI focus management; bell label with live count; WCAG 2.1 AA via MUI v6 defaults |

**Constitution Check: PASS — no violations. Proceed to Phase 1.**

### Post-Design Re-check (Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| II. SOLID — O/C | ✅ PASS | New event types added to `EventType` enum without modifying dispatch logic |
| II. SOLID — D | ✅ PASS | `NotificationService` depends on `INotificationRepository` interface, not `SQLiteNotificationRepository` directly |
| III. DRY | ✅ PASS | Filter evaluation logic lives only in `RuleEngine._evaluate_filter()` |
| IV. Security | ✅ PASS | SSE token validated against session store; no user can receive another user's SSE events |

---

## Project Structure

### Documentation (this feature)

```text
specs/008-notifications/
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
│   ├── main.py                        # FastAPI app, lifespan handler, scheduler start
│   ├── core/
│   │   ├── config.py                  # Settings (Pydantic BaseSettings)
│   │   ├── database.py                # Async engine, session factory, Base
│   │   └── security.py                # Auth dependency (get_current_user)
│   ├── models/
│   │   └── notification.py            # ORM: Notification, NotificationPreference, AdminNotificationRule
│   ├── schemas/
│   │   └── notification.py            # Pydantic v2 request/response schemas
│   ├── repositories/
│   │   ├── base.py                    # INotificationRepository (abstract)
│   │   └── sqlite_notification_repository.py
│   ├── services/
│   │   ├── notification_service.py    # Business logic: create, read, mark-read, digest
│   │   ├── rule_engine.py             # In-process rule cache + filter evaluation
│   │   └── sse_manager.py             # Per-user asyncio.Queue fan-out
│   ├── scheduler/
│   │   └── jobs.py                    # APScheduler: purge job, digest flush job
│   └── api/
│       └── v1/
│           ├── notifications.py       # CRUD + mark-read endpoints
│           ├── sse.py                 # GET /sse EventSourceResponse
│           ├── preferences.py         # GET/PUT /preferences/notifications
│           ├── admin_rules.py         # Admin CRUD for notification rules
│           └── _test.py               # Test-only emit + run-purge endpoints (disabled in prod)
└── tests/
    ├── unit/
    │   ├── test_rule_engine.py
    │   ├── test_notification_service.py
    │   └── test_digest_flush.py
    └── integration/
        ├── test_notifications_api.py
        ├── test_sse_endpoint.py
        └── test_preferences_api.py

frontend/
├── src/
│   ├── types/
│   │   └── notification.ts            # Shared TS types (EventType enum, Notification, etc.)
│   ├── services/
│   │   └── notificationApi.ts         # Axios wrappers for all notification endpoints
│   ├── hooks/
│   │   ├── useEventSource.ts          # Custom SSE hook (reconnect, cleanup)
│   │   ├── useNotifications.ts        # TanStack Query: infinite list + badge count
│   │   └── useInfiniteScroll.ts       # IntersectionObserver hook for panel scroll
│   ├── store/
│   │   └── notificationContext.tsx    # Context + useReducer (add/read/clear actions)
│   ├── components/
│   │   └── notifications/
│   │       ├── NotificationBell.tsx   # IconButton + Badge + panel anchor
│   │       ├── NotificationPanel.tsx  # MUI Menu/Popover + infinite scroll list
│   │       ├── NotificationItem.tsx   # Single row: icon, title, timestamp, read state
│   │       └── NotificationBadge.tsx  # aria-live badge counter
│   └── pages/
│       ├── NotificationSettingsPage.tsx  # Per-event-type toggle switches
│       └── AdminRulesPage.tsx            # Admin CRUD table for org-wide rules
└── tests/
    ├── NotificationBell.test.tsx
    ├── NotificationPanel.test.tsx
    ├── NotificationSettingsPage.test.tsx
    └── useEventSource.test.ts
```

**Structure Decision**: Web application (Option 2) — separate `backend/` and `frontend/` top-level directories. Backend is a standalone FastAPI service; frontend is a Vite + React SPA. Both co-located in the monorepo root.

---

## Complexity Tracking

> No constitution violations — table left empty intentionally.

---

## Key Design Decisions

### SSE Fan-Out Architecture

```
Event source (any module)
    │
    ▼
NotificationService.dispatch(event)
    │
    ├─► Filter: check NotificationPreference for each recipient
    │
    ├─► Filter: evaluate AdminNotificationRules (in-process cache)
    │
    └─► For each recipient:
            Insert Notification row
            SSEManager.publish(user_id, SSEEvent)
                └─► asyncio.Queue.put() for each active connection
```

### Admin Rule Evaluation (in-process)

```python
class RuleEngine:
    _rules: list[AdminNotificationRule] = []   # reloaded on CRUD

    def evaluate(self, event_type: str, context: dict) -> list[int]:
        """Returns list of user_ids to notify via admin rules."""
        matched = [r for r in self._rules if r.event_type == event_type and r.is_enabled]
        results = []
        for rule in matched:
            if rule.filter_field and not self._evaluate_filter(rule, context):
                continue
            results.extend(self._resolve_targets(rule))
        return results
```

### Digest Flush (APScheduler, 60-second interval)

1. Query: `SELECT user_id, event_type, source_record_type, COUNT(*) FROM notifications WHERE is_digest=FALSE AND created_at > NOW()-60s GROUP BY ... HAVING COUNT(*) >= 10`.
2. For each group: `UPDATE` first row to `is_digest=TRUE, digest_count=N`; `DELETE` remaining N-1 rows.
3. Emit `notification.refresh` SSE event to affected users.

### React Notification Context

```typescript
type NotificationAction =
  | { type: 'ADD'; notification: Notification }
  | { type: 'READ'; id: number }
  | { type: 'READ_ALL' }
  | { type: 'REFRESH_COUNT'; count: number };
```

SSE `notification.new` → dispatch `ADD`.
SSE `notification.refresh` → dispatch `REFRESH_COUNT` + TanStack Query `invalidate`.
