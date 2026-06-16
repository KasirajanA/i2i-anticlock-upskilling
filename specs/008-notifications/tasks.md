# Tasks: Notifications & Alerts (Module 008)

**Input**: Design documents from `specs/008-notifications/`

**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/api.md ✅ quickstart.md ✅

**Tests**: Not included — not requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks in same phase)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in every description

## Path Conventions

- Backend: `backend/app/`, `backend/alembic/`
- Frontend: `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install new runtime dependencies and create the DB migration before any feature code runs.

- [ ] T001 Add `sse-starlette>=1.6` and `apscheduler[asyncio]>=4.0` to backend/requirements.txt and pin exact versions
- [ ] T002 Create Alembic migration 008_notifications.py: CREATE TABLE notifications (id PK AUTOINCREMENT, user_id FK→users NOT NULL, event_type TEXT NOT NULL, title TEXT NOT NULL, body TEXT NULLABLE, source_record_type TEXT NULLABLE, source_record_id INTEGER NULLABLE, is_read BOOLEAN NOT NULL DEFAULT FALSE, is_digest BOOLEAN NOT NULL DEFAULT FALSE, digest_count INTEGER NOT NULL DEFAULT 1, admin_rule_id FK→admin_notification_rules NULLABLE ON DELETE SET NULL, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, expires_at DATETIME NOT NULL; indexes ix_notif_user_read_created on user_id+is_read+created_at, ix_notif_expires on expires_at, ix_notif_digest_window on user_id+event_type+source_record_type+created_at); CREATE TABLE notification_preferences (id PK, user_id FK→users NOT NULL, event_type TEXT NOT NULL, is_enabled BOOLEAN NOT NULL DEFAULT TRUE, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP; UNIQUE(user_id, event_type)); CREATE TABLE admin_notification_rules (id PK, name TEXT NOT NULL, event_type TEXT NOT NULL, filter_field TEXT NULLABLE, filter_operator TEXT NULLABLE, filter_value TEXT NULLABLE, target_type TEXT NOT NULL, target_value TEXT NOT NULL, is_enabled BOOLEAN NOT NULL DEFAULT TRUE, created_by FK→users NOT NULL, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP; index on event_type+is_enabled) in backend/alembic/versions/008_notifications.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: ORM models, schemas, abstract repository interface, TypeScript types, SSEManager, and SQLite WAL mode — all shared across every user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T003 [P] Create EventType StrEnum (ASSIGNMENT, COMMENT, MENTION, STATUS_CHANGE, CONTRACT_RENEWAL_DUE, DEAL_STAGE_CHANGE, SLA_BREACH) and three SQLAlchemy 2.x ORM models using Mapped/mapped_column syntax: Notification (all 13 columns with types, FKs, 3 Index table_args), NotificationPreference (5 columns, UniqueConstraint on user_id+event_type), AdminNotificationRule (15 columns, index on event_type+is_enabled) in backend/app/models/notification.py
- [ ] T004 [P] Define all Pydantic v2 schemas: NotificationResponse (all Notification fields), PaginatedNotifications (items: list[NotificationResponse], next_cursor: int | None, unread_count: int), UnreadCountResponse (count: int), MarkReadResponse (id, is_read), MarkAllReadResponse (updated_count: int), PreferenceItem (event_type: str, is_enabled: bool), PreferencesResponse (preferences: list[PreferenceItem]), UpdatePreferencesRequest (preferences: list[PreferenceItem] validated for no duplicate event_types and all values in EventType enum), AdminRuleResponse (all AdminNotificationRule fields), CreateRuleRequest (name, event_type, filter_field nullable, filter_operator nullable, filter_value nullable, target_type, target_value; validator: filter_field/operator/value must all be present or all absent), UpdateRuleRequest (all fields optional) in backend/app/schemas/notification.py
- [ ] T005 [P] Define INotificationRepository abstract base class with abstract async methods: get_list, get_unread_count, mark_read, mark_all_read, create_notification, get_preferences, upsert_preferences, list_rules, create_rule, update_rule, delete_rule, purge_expired, flush_digest_groups — each with typed signatures matching their SQLite implementation in backend/app/repositories/base.py
- [ ] T006 [P] Define TypeScript types: EventType enum (7 string values matching backend StrEnum), Notification interface (id, event_type, title, body, source_record_type, source_record_id, is_read, is_digest, digest_count, created_at), PaginatedNotifications, PreferenceItem (event_type: EventType, is_enabled: boolean), PreferencesResponse, AdminRule interface (all admin_notification_rules fields), CreateRuleRequest, NotificationState {items: Notification[], unreadCount: number} in frontend/src/types/notification.ts
- [ ] T007 [P] Implement SSEManager singleton: private _connections: Map<number, Set<asyncio.Queue>>; async publish(user_id: int, event_type: str, data: dict) → None (puts SSEEvent onto all queues for that user, no-op if no queues); register(user_id: int) → asyncio.Queue (creates Queue, adds to Set for user_id); unregister(user_id: int, queue: asyncio.Queue) → None (removes queue, cleans up empty Sets); export sse_manager singleton instance in backend/app/services/sse_manager.py
- [ ] T008 [P] Add SQLite WAL mode configuration to the async engine setup: use SQLAlchemy `@event.listens_for(engine.sync_engine, "connect")` to execute `PRAGMA journal_mode=WAL` and `PRAGMA synchronous=NORMAL` on each new raw DBAPI connection; import and call this setup in database init so it applies to the shared engine in backend/app/core/database.py

**Checkpoint**: Foundation ready — all three user stories can now begin.

---

## Phase 3: User Story 1 — In-App Notifications (Priority: P1) 🎯 MVP

**Goal**: Real-time notification bell badge updates via SSE within 5 seconds of a triggering event; notification panel shows cursor-paginated list; mark-read and mark-all-read work; APScheduler runs digest flush (60 s) and purge (30-day) jobs.

**Independent Test**: Using `POST /api/v1/_test/emit`, fire an `assignment` event for a logged-in user — confirm bell badge increments within 5 s; open panel, confirm the item links to the correct source record; click "Mark all as read" — confirm badge clears to 0.

### Implementation for User Story 1

- [ ] T009 [P] [US1] Implement SQLiteNotificationRepository (extends INotificationRepository): get_list(user_id, limit=20, cursor=None, unread_only=False) → PaginatedNotifications (SELECT … WHERE user_id=:uid [AND is_read=False] [AND id < :cursor] ORDER BY id DESC LIMIT :limit; next_cursor = last item id if len(items)=limit else None; unread_count from separate COUNT query); get_unread_count(user_id) → int (SELECT COUNT WHERE user_id=:uid AND is_read=False); mark_read(user_id, notification_id) → Notification (UPDATE SET is_read=True WHERE id=:id AND user_id=:uid; raises 404 if not found); mark_all_read(user_id) → MarkAllReadResponse (UPDATE SET is_read=True WHERE user_id=:uid AND is_read=False; return {updated_count: rowcount}); create_notification(user_id, event_type, title, body, source_record_type, source_record_id, admin_rule_id=None) → Notification (INSERT with expires_at = utcnow() + timedelta(days=30)); purge_expired() → int (DELETE WHERE expires_at < utcnow(); return rowcount); flush_digest_groups() → list[int] (SELECT user_id, event_type, source_record_type, MIN(id) AS keep_id, COUNT(*) AS cnt FROM notifications WHERE is_digest=FALSE AND created_at >= utcnow()-60s GROUP BY user_id, event_type, source_record_type HAVING cnt >= 10; for each group: UPDATE id=keep_id SET is_digest=True, digest_count=cnt; DELETE WHERE user_id=:uid AND event_type=:et AND source_record_type=:srt AND is_digest=FALSE AND id != keep_id; return list of unique affected user_ids) in backend/app/repositories/sqlite_notification_repository.py
- [ ] T010 [US1] Implement NotificationService: __init__(repo: INotificationRepository, sse_manager: SSEManager); dispatch(event_type: str, title: str, body: str | None, source_record_type: str | None, source_record_id: int | None, target_user_ids: list[int], bypass_preferences: bool = False, admin_rule_id: int | None = None) → None (for each user_id: if not bypass_preferences check NotificationPreference row → skip if is_enabled=False; call repo.create_notification → notification; await sse_manager.publish(user_id, "notification.new", {id, event_type, title, unread_count: await repo.get_unread_count(user_id)})); get_list(user_id, limit, cursor, unread_only) → PaginatedNotifications (delegates to repo); get_unread_count(user_id) → int; mark_read(user_id, notification_id) → Notification; mark_all_read(user_id) → MarkAllReadResponse in backend/app/services/notification_service.py
- [ ] T011 [P] [US1] Implement APScheduler jobs module: configure AsyncScheduler with AsyncSQLAlchemyJobStore pointing to same SQLite DB file path; define async purge_job() function calling repo.purge_expired() + logging result; define async digest_flush_job() function calling user_ids = repo.flush_digest_groups(); for each affected user_id: await sse_manager.publish(user_id, "notification.refresh", {unread_count: repo.get_unread_count(user_id)}); export scheduler instance and add_jobs(scheduler, repo, sse_manager) helper that registers purge_job with CronTrigger(hour=2) and digest_flush_job with IntervalTrigger(seconds=60) in backend/app/scheduler/jobs.py
- [ ] T012 [P] [US1] Update FastAPI app lifespan context manager in backend/app/main.py: on startup await scheduler.start() and call add_jobs(scheduler, repo, sse_manager); on shutdown await scheduler.shutdown(wait=False); import and include routers for notifications, sse, and _test with prefix=/api/v1; leave stubs for preferences and admin_rules routers (to be added in US2/US3 phases) in backend/app/main.py
- [ ] T013 [P] [US1] Implement all notification CRUD API endpoints: GET /api/v1/notifications (query params: limit int=20 max 50, cursor int optional, unread_only bool=False; returns PaginatedNotifications), GET /api/v1/notifications/unread-count (returns UnreadCountResponse), PATCH /api/v1/notifications/{id}/read (returns MarkReadResponse; 404 if not owned by current user), POST /api/v1/notifications/mark-all-read (returns MarkAllReadResponse) in backend/app/api/v1/notifications.py
- [ ] T014 [P] [US1] Implement GET /api/v1/sse SSE endpoint: validate `token` query param using get_current_user_from_token (raises HTTP 401 for invalid/expired tokens — critical security check per FR-004); on valid auth: queue = sse_manager.register(user_id); if Last-Event-ID header set, query DB for notifications with id > last_event_id and yield them immediately; return EventSourceResponse(generator) where generator: loops forever dequeueing from queue (asyncio.wait_for with 30s timeout), on timeout yields {"event": "ping", "data": "{}"}, on data yields SSE event; on generator close: sse_manager.unregister(user_id, queue) in backend/app/api/v1/sse.py
- [ ] T015 [P] [US1] Implement test-only router (guarded by `if settings.ENV != "production": app.include_router(...)`): POST /api/v1/_test/emit accepts {user_id, event_type, title, source_record_type, source_record_id} body and directly calls repo.create_notification + sse_manager.publish bypassing preferences (for quickstart.md validation); POST /api/v1/_test/run-purge calls repo.purge_expired() synchronously and returns {deleted: N} in backend/app/api/v1/_test.py
- [ ] T016 [P] [US1] Create notificationApi.ts Axios service: import crm_session-enabled Axios instance from existing service base; add getNotifications(params: {limit?, cursor?, unread_only?}) → Promise<PaginatedNotifications>, getUnreadCount() → Promise<UnreadCountResponse>, markRead(id: number) → Promise<MarkReadResponse>, markAllRead() → Promise<MarkAllReadResponse>; export SSE_URL helper: (token: string) => `${baseURL}/api/v1/sse?token=${encodeURIComponent(token)}` in frontend/src/services/notificationApi.ts
- [ ] T017 [P] [US1] Implement notificationContext.tsx: NotificationState {items: Notification[], unreadCount: number, lastEventId: number | null}; notificationReducer handling ADD (prepend to items, increment unreadCount, update lastEventId), READ (find by id, set is_read=true, decrement unreadCount), READ_ALL (map all items to is_read=true, set unreadCount=0), REFRESH_COUNT (set unreadCount, clear items triggering refetch); NotificationProvider React component wrapping children with Context.Provider; export useNotificationContext() hook in frontend/src/store/notificationContext.tsx
- [ ] T018 [P] [US1] Implement useEventSource custom React hook: accepts SSE URL string; creates EventSource on mount; handles onmessage: parse event.type and event.data, dispatch ADD or REFRESH_COUNT to NotificationContext; implements exponential back-off reconnect on onerror (1s, 2s, 4s, 8s … max 30s); resets back-off on onopen; closes EventSource and clears retry timers on unmount; handles "ping" events by no-op in frontend/src/hooks/useEventSource.ts
- [ ] T019 [P] [US1] Create useNotifications TanStack Query hook: useNotificationList() using useInfiniteQuery with queryKey ["notifications"], queryFn calling getNotifications with pageParam as cursor, initialPageParam undefined, getNextPageParam returning next_cursor (null → stops), staleTime 30_000; useUnreadCount() using useQuery with queryKey ["notifications","count"], queryFn calling getUnreadCount; useMarkRead() mutation invalidating ["notifications"] and ["notifications","count"] on settle; useMarkAllRead() mutation invalidating both query keys on settle in frontend/src/hooks/useNotifications.ts
- [ ] T020 [P] [US1] Implement useInfiniteScroll hook: accepts ref to sentinel element and onLoadMore callback; creates IntersectionObserver with threshold 0.1 observing the sentinel; calls onLoadMore() when entry.isIntersecting is true; cleans up observer on unmount; accepts optional disabled boolean prop to stop observation when hasNextPage is false in frontend/src/hooks/useInfiniteScroll.ts
- [ ] T021 [P] [US1] Implement NotificationBadge component: MUI Badge wrapping children prop with badgeContent set to unreadCount from useUnreadCount (max 99 shown as "99+"); invisible when count=0; aria-label={`${count} unread notifications`}; add a visually-hidden aria-live="polite" span outside the badge that announces count changes (e.g., "3 new notifications") for screen reader compatibility (WCAG research.md §8) in frontend/src/components/notifications/NotificationBadge.tsx
- [ ] T022 [P] [US1] Implement NotificationItem component: MUI ListItem with ListItemIcon (event-type icon: assignment→AssignmentIndIcon, comment→CommentIcon, mention→AlternateEmailIcon, status_change→SwapHorizIcon, contract_renewal_due→AutorenewIcon, deal_stage_change→TrendingUpIcon, sla_breach→WarningAmberIcon), ListItemText primary={title} with bold fontWeight when !is_read, secondary={relative timestamp using date-fns formatDistanceToNow + source_record_type label}; MUI Link to /[source_record_type]s/[source_record_id] when both present; MUI Chip size="small" label={`${digest_count} items`} when is_digest=true and digest_count>1; onClick calls useMarkRead(id) in frontend/src/components/notifications/NotificationItem.tsx
- [ ] T023 [P] [US1] Implement NotificationPanel component: MUI Popover anchored to anchorEl prop (bell icon button); MUI MenuList with role="menu" and aria-label="Notifications"; header MUI Typography "Notifications" + "Mark all as read" MUI Button (calls useMarkAllRead, disabled when unreadCount=0); MUI List of NotificationItem components from flattened useNotificationList pages; invisible sentinel div at bottom of list with useInfiniteScroll calling fetchNextPage when hasNextPage; MUI CircularProgress when isFetchingNextPage; "No notifications" MUI Typography empty state; keyboard: Escape key handler calling onClose in frontend/src/components/notifications/NotificationPanel.tsx
- [ ] T024 [US1] Implement NotificationBell component: MUI IconButton aria-label={`Notifications, ${unreadCount} unread`} onClick toggles panelOpen state; wraps MUI NotificationsIcon with NotificationBadge component; MUI Fade-transitioned NotificationPanel with anchorEl set to bell button ref when panelOpen; calls useEventSource(SSE_URL(sessionToken)) to start SSE subscription; registers NotificationProvider context actions in frontend/src/components/notifications/NotificationBell.tsx
- [ ] T025 [US1] Integrate NotificationBell into app: wrap root component in NotificationProvider in frontend/src/main.tsx; add NotificationBell to the MUI AppBar right-side toolbar in the main layout component (likely frontend/src/App.tsx or a dedicated Layout component); add /notifications/settings placeholder route and /admin/notification-rules placeholder route for later stories in frontend/src/App.tsx

**Checkpoint**: User Story 1 independently testable — run quickstart.md Scenarios SC-001 (badge ≤5 s) and SC-002 (pending on login ≤2 s) using the `_test/emit` endpoint to validate.

---

## Phase 4: User Story 2 — Notification Preferences (Priority: P2)

**Goal**: Any logged-in user can open Notification Settings, toggle each of the 7 event types on or off, and subsequent events of disabled types generate no notification for that user.

**Independent Test**: Disable "comment" preference, call `POST /api/v1/_test/emit` with event_type=comment, confirm badge does NOT increment; emit an "assignment" event, confirm badge DOES increment.

### Implementation for User Story 2

- [ ] T026 [P] [US2] Add preference methods to SQLiteNotificationRepository: async get_preferences(user_id: int) → list[PreferenceItem] (SELECT from notification_preferences WHERE user_id=:uid; for any EventType not in results return a synthetic PreferenceItem with is_enabled=True — application-level default); async upsert_preferences(user_id: int, preferences: list[PreferenceItem]) → list[PreferenceItem] (INSERT OR REPLACE into notification_preferences for each item; set updated_at=utcnow(); return updated full list via get_preferences) in backend/app/repositories/sqlite_notification_repository.py
- [ ] T027 [P] [US2] Implement GET /api/v1/preferences/notifications (returns PreferencesResponse with one item per EventType enum value; missing DB rows filled with is_enabled=True) and PUT /api/v1/preferences/notifications (validates no duplicate event_types, validates all event_types in EventType enum, calls repo.upsert_preferences, returns updated PreferencesResponse); register preferences router with prefix=/api/v1 in backend/app/main.py in backend/app/api/v1/preferences.py
- [ ] T028 [P] [US2] Add getPreferences() → Promise<PreferencesResponse> and updatePreferences(body: UpdatePreferencesRequest) → Promise<PreferencesResponse> typed Axios functions to frontend/src/services/notificationApi.ts
- [ ] T029 [P] [US2] Implement NotificationSettingsPage: MUI Paper container with title "Notification Settings"; MUI List of 7 rows — one per EventType; each row has ListItemText with human-readable label (assignment → "Record Assignments", comment → "Comments", mention → "Mentions", status_change → "Status Changes", contract_renewal_due → "Contract Renewal Reminders", deal_stage_change → "Deal Stage Changes", sla_breach → "SLA Breach Alerts") and secondary description text; MUI Switch controlled by is_enabled from useQuery (getPreferences); onChange debounced 500 ms auto-saves via useMutation (updatePreferences sending only the changed entry); MUI Snackbar "Preferences saved" on success; MUI CircularProgress while loading in frontend/src/pages/NotificationSettingsPage.tsx
- [ ] T030 [US2] Update /notifications/settings placeholder route in React Router to render NotificationSettingsPage; add "Notification Settings" MUI MenuItem to user profile dropdown menu in the AppBar layout component in frontend/src/App.tsx

**Checkpoint**: User Story 2 independently testable — run quickstart.md Scenario SC-003 (preferences toggle) to validate.

---

## Phase 5: User Story 3 — Admin Notification Rules (Priority: P2)

**Goal**: Admin creates organisation-wide notification rules (event type + optional filter condition + target role/user); rules fire on every matching event dispatch regardless of individual user preferences; enabling/disabling a rule takes immediate effect via in-process cache.

**Independent Test**: Admin creates rule `event_type=deal_stage_change, filter_field=deal_value, filter_operator=>, filter_value=10000, target_type=role, target_value=Admin`. Emit `deal_stage_change` with `deal_value=15000` via `_test/emit`. Confirm Admin user receives the notification even if they had deal_stage_change disabled in preferences.

### Implementation for User Story 3

- [ ] T031 [P] [US3] Add rule methods to SQLiteNotificationRepository: async list_rules(enabled_only: bool = False) → list[AdminNotificationRule] (SELECT all rows, optionally filter WHERE is_enabled=TRUE); async create_rule(data: CreateRuleRequest, created_by_id: int) → AdminNotificationRule (INSERT; sets created_at, updated_at); async update_rule(rule_id: int, data: UpdateRuleRequest) → AdminNotificationRule (UPDATE partial fields; set updated_at=utcnow()); async delete_rule(rule_id: int) → None (DELETE by id; past notifications retain admin_rule_id=NULL via ON DELETE SET NULL) in backend/app/repositories/sqlite_notification_repository.py
- [ ] T032 [US3] Implement RuleEngine: _rules: list[AdminNotificationRule] = [] held in memory; async reload(repo: INotificationRepository) → None (awaits repo.list_rules(enabled_only=True); replaces _rules); evaluate(event_type: str, context: dict) → list[int] (filter _rules by event_type and is_enabled; for each matching rule: if filter_field set call _evaluate_filter(rule, context) → skip rule if False; call _resolve_targets(rule) → list[int]: target_type="role" → query users table for all user_ids with that role; target_type="user" → [int(target_value)]); _evaluate_filter(rule, context) → bool (cast context.get(rule.filter_field) to float for numeric ops or str for "=" and "in"; apply filter_operator: >, <, =, >=, <=, in; return False if filter_field missing from context; raise ValueError for unknown operator); export rule_engine singleton instance in backend/app/services/rule_engine.py
- [ ] T033 [US3] Integrate RuleEngine into NotificationService: update dispatch() to additionally call rule_engine.evaluate(event_type, context) → admin_user_ids; union with user-preference recipients; for admin-rule recipient user_ids call create_notification with bypass_preferences=True and admin_rule_id=matching_rule.id; SSEManager.publish for all recipients; ensure context dict is passed as new parameter to dispatch() in backend/app/services/notification_service.py
- [ ] T034 [P] [US3] Implement all Admin notification rule endpoints with require_module_access("user_team_management") Admin-only guard: GET /api/v1/admin/notification-rules (list all rules), POST /api/v1/admin/notification-rules (create; validate filter_field/operator/value all-or-none; validate target_type=role → valid role name; target_type=user → parseable int user_id; returns 201 rule object), PATCH /api/v1/admin/notification-rules/{id} (partial update is_enabled or any field; call rule_engine.reload() after success), DELETE /api/v1/admin/notification-rules/{id} (delete; call rule_engine.reload(); return 204); register admin_rules router with prefix=/api/v1 in backend/app/main.py; call rule_engine.reload() once in FastAPI lifespan startup in backend/app/api/v1/admin_rules.py
- [ ] T035 [P] [US3] Add list_rules(), create_rule(body: CreateRuleRequest), update_rule(id: number, body: UpdateRuleRequest), delete_rule(id: number) typed Axios functions to frontend/src/services/notificationApi.ts
- [ ] T036 [P] [US3] Implement AdminRulesPage: MUI DataGrid/Table with columns name, event_type (formatted label), filter summary (e.g., "deal_value > 10000" or "—"), target (e.g., "role: Admin"), is_enabled MUI Switch (calls update_rule on toggle), actions (Edit MUI IconButton, Delete MUI IconButton); "New Rule" MUI Button opens MUI Dialog with form: name MUI TextField, event_type MUI Select (7 options), filter_field MUI Select (optional: deal_value, priority, status, source_record_type), filter_operator MUI Select (shown when filter_field set: >, <, =, >=, <=, in), filter_value MUI TextField (shown when filter_field set), target_type MUI RadioGroup (role / specific user), target_value MUI Select for role or MUI Autocomplete for user; edit dialog pre-populates; delete MUI Dialog confirmation in frontend/src/pages/AdminRulesPage.tsx
- [ ] T037 [US3] Update /admin/notification-rules placeholder route to render AdminRulesPage wrapped in RequireRole (Admin only); add "Notification Rules" MUI MenuItem to Admin navigation section in frontend/src/App.tsx

**Checkpoint**: User Story 3 independently testable — run quickstart.md "Admin Rule" scenario to validate.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: WCAG accessibility verification, SSE security audit, linting, and full end-to-end validation.

- [ ] T038 [P] Verify and complete WCAG 2.1 AA accessibility: (1) NotificationBell has aria-label="Notifications, N unread" updating on count change; (2) NotificationBadge has role="status" span; (3) aria-live="polite" region is placed OUTSIDE the bell button in App.tsx and announces new notification count; (4) NotificationPanel has role="dialog" aria-label="Notifications", focus moves to panel on open, Escape key closes panel; (5) NotificationItem links have descriptive aria-labels; (6) keyboard navigation works through all panel items in frontend/src/components/notifications/
- [ ] T039 [P] Audit SSE endpoint security: verify get_current_user_from_token in sse.py raises HTTP 401 for missing, expired, and invalid tokens; verify SSEManager.publish is keyed strictly by user_id so User A's queue never receives User B's events; add a test note confirming no cross-user event leakage is possible in backend/app/api/v1/sse.py
- [ ] T040 [P] Run Ruff linter (ruff check backend/app/) and fix all violations in all new backend/app/ files added in this module
- [ ] T041 [P] Run ESLint (npx eslint frontend/src/) and tsc --noEmit and fix all violations in all new frontend/src/ files added in this module
- [ ] T042 Run quickstart.md Scenarios SC-001 through SC-005 end-to-end: SC-001 (badge ≤5 s via _test/emit), SC-002 (pending notifications on login ≤2 s), SC-003 (preference toggle suppresses events), SC-004 (15 bulk emits → single digest after 60 s), SC-005 (run-purge removes expired notification); document any failures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — run `pip install` and `alembic upgrade head` first
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all three user stories
- **US1 (Phase 3)**: Depends on Phase 2 completion — core delivery mechanism
- **US2 (Phase 4)** and **US3 (Phase 5)**: Both depend on Phase 2; US2 and US3 can run in parallel if staffed; US3's RuleEngine integrates into NotificationService (T033) which extends T010 from US1
- **Polish (Phase 6)**: Depends on all desired stories being complete

### User Story Dependencies

- **US1 (P1)**: No dependency on US2 or US3 — independently testable with `_test/emit`
- **US2 (P2)**: No dependency on US1 backend; adds preference rows checked by NotificationService.dispatch already written in T010 — independently testable
- **US3 (P2)**: Depends on US1 (T010 NotificationService exists) for T033 integration; RuleEngine (T032) is independently writable but only active after T033 integrates it

### Within Each User Story

- Repository → Service → Router (backend layer ordering)
- notificationApi → Context/Hooks → Leaf components → Page/Bell → App integration (frontend)
- T009 (repo) must complete before T010 (service) can be finalised
- T023 (NotificationPanel) must complete before T024 (NotificationBell) assembles it
- T024 (NotificationBell) must complete before T025 (App integration) mounts it

---

## Parallel Execution Examples

### Phase 2 Parallel Block (all 6 tasks concurrently)

```
T003  ORM models + EventType enum (models/notification.py)
T004  Pydantic schemas (schemas/notification.py)
T005  Abstract repository interface (repositories/base.py)
T006  TypeScript types (types/notification.ts)
T007  SSEManager singleton (services/sse_manager.py)
T008  SQLite WAL mode (core/database.py)
```

### Phase 3 Parallel Block — backend leaf + all frontend files

```
T009  SQLiteNotificationRepository (repositories/sqlite_notification_repository.py)
T011  APScheduler jobs (scheduler/jobs.py)
T012  main.py lifespan + router registration
T013  notifications.py router (api/v1/notifications.py)
T014  sse.py SSE endpoint (api/v1/sse.py)
T015  _test.py test-only endpoints (api/v1/_test.py)
T016  notificationApi.ts Axios functions
T017  notificationContext.tsx Context + useReducer
T018  useEventSource.ts SSE hook
T019  useNotifications.ts TanStack Query hook
T020  useInfiniteScroll.ts IntersectionObserver hook
T021  NotificationBadge.tsx aria-live component
T022  NotificationItem.tsx single row component
T023  NotificationPanel.tsx infinite-scroll panel
```

14 tasks across 14 different files — write all simultaneously, then T010 (service), T024 (bell), T025 (App integration) sequentially.

### Phase 4 Parallel Block

```
T026  Preference methods in sqlite_notification_repository.py
T027  preferences.py router + main.py registration
T028  notificationApi.ts preferences functions
T029  NotificationSettingsPage.tsx
```

Four tasks across four different files — then T030 (App route) sequentially.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T008)
3. Complete Phase 3: User Story 1 (T009–T025)
4. **STOP and VALIDATE**: quickstart.md SC-001 and SC-002
5. Deploy/demo — real-time badge, SSE, mark-read, digest batching, 30-day purge all working

### Incremental Delivery

1. Phase 1 + 2 → Foundation ready
2. US1 complete → Real-time notifications live (MVP)
3. US2 complete → Users can tune their notification signal-to-noise ratio
4. US3 complete → Business-critical Admin rules fire regardless of personal preferences
5. Polish → WCAG AA verified, security audited, all SC criteria confirmed

### Parallel Team Strategy

After Phase 2 completes:
- **Dev A**: User Story 1 (T009–T025) — backend SSE + scheduler + frontend bell
- **Dev B**: User Story 2 (T026–T030) — preferences API + settings page
- **Dev C**: User Story 3 (T031–T037) — rule engine + admin rules UI (can start T031/T032 independent of US1 completion; T033 waits for T010)

---

## Notes

- [P] = different file from all other [P] tasks in the same phase; safe to run concurrently
- [US1/US2/US3] = maps task to user story for traceability and independent delivery
- T002 (Alembic migration) must be applied (`alembic upgrade head`) before any story code runs
- T007 (SSEManager) is a **singleton** — import the module-level `sse_manager` instance in T010, T013, T014 rather than instantiating a new one per request
- T008 (WAL mode) extends the existing database.py from Module 005 — read the file before editing to avoid overwriting existing engine setup
- T012 (main.py) updates the existing FastAPI app from previous modules — read current lifespan handler before adding scheduler logic
- T010 (NotificationService.dispatch) is extended in T033 (US3) — T033 adds context parameter and RuleEngine call; ensure backward compatibility with all existing dispatch callers
- T015 (_test.py) MUST be guarded by `settings.ENV != "production"` — never expose raw notification emit or purge-trigger in production
- T014 (SSE endpoint) uses a query-param token because browser `EventSource` API cannot set `Authorization` headers; validate this token strictly against the session store (same validation as cookie-based auth)
- SSEManager pub/sub is in-process only (no Redis); this is sufficient for SQLite-scale ≤1,000 concurrent users per plan.md constraints
