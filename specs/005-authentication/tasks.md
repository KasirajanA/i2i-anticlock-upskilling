# Tasks: Authentication

**Feature Branch**: `005-authentication`
**Input**: Design documents from `specs/005-authentication/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/api.md ✅, quickstart.md ✅

**Key constraint**: No JWT, no localStorage — `HttpOnly; Secure; SameSite=Strict` cookie only. bcrypt cost factor exactly 12. MFA, SSO, RBAC out of scope v1.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[US#]**: Maps to user story from spec.md
- Each task includes exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project skeleton per plan.md structure

- [X] T001 Create backend directory structure: `backend/app/{core,models,schemas,repositories,services,middleware,api/v1}`, `backend/tests/{unit,integration}`
- [X] T002 [P] Create frontend directory structure: `frontend/src/{types,context,hooks,components/auth,pages}`, `frontend/tests/`
- [X] T003 [P] Add `passlib[bcrypt]` to `backend/requirements.txt` (new dependency for this module)
- [X] T004 [P] Verify `react-router-dom` v6 is in `frontend/package.json`; add if missing

**Checkpoint**: Project skeleton ready — ready to wire up ORM and services

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: ORM models, migration, schemas, PasswordHasher, AuthContext skeleton, and API router stubs — MUST be complete before any user story

**⚠️ CRITICAL**: T005→T006→T007→T008 are strictly sequential (each depends on the previous); T009 onward may start after T007

- [X] T005 Create `backend/app/core/config.py`: `Settings` class (pydantic-settings) with `SESSION_TIMEOUT_MINUTES: int = 30`, `BCRYPT_ROUNDS: int = 12`, `ENVIRONMENT: str = "development"` read from env vars
- [X] T006 Create `backend/app/core/database.py`: async SQLAlchemy engine with WAL mode (`PRAGMA journal_mode=WAL`), `AsyncSession` factory, `get_async_session` dependency
- [X] T007 Create ORM models `User`, `Session`, `FailedLoginAttempt` in `backend/app/models/auth.py`: all columns, constraints, and indexes from data-model.md; `User.role` as `VARCHAR(20)` with `RoleEnum` StrEnum; `Session.session_id` as `VARCHAR(36)` UUID4 PK
- [X] T008 Generate and apply Alembic migration: `alembic revision --autogenerate -m "auth_tables"` → inspect generated SQL → `alembic upgrade head` (creates `users`, `sessions`, `failed_login_attempts`)
- [X] T009 [P] Create all Pydantic v2 schemas in `backend/app/schemas/auth.py`: `LoginRequest`, `CreateUserRequest` (email, password, role, display_name), `ResetPasswordRequest`, `UserResponse`, `MeResponse`; email validator normalises to lowercase; `model_config = ConfigDict(from_attributes=True)`
- [X] T010 [P] Create `IUserRepository` abstract base class with method stubs (`create`, `get_by_email`, `get_by_id`, `list_all`) and `SqliteUserRepository` concrete skeleton in `backend/app/repositories/base.py` and `backend/app/repositories/sqlite_user_repository.py`
- [X] T011 [P] Create `PasswordHasher` with `async hash(password: str) -> str`, `async verify(password: str, hashed: str) -> bool`, `async dummy_verify() -> None` all using `run_in_executor(None, ...)` to avoid blocking event loop; `CryptContext(schemes=["bcrypt"], bcrypt__rounds=12)` in `backend/app/services/password_hasher.py`
- [X] T012 [P] Create `backend/app/core/seed.py`: idempotent initial Admin seed — reads `SEED_ADMIN_EMAIL` + `SEED_ADMIN_PASSWORD` from env, creates Admin user if no Admin exists; running twice produces no duplicate (Constitution IV: no hardcoded credentials)
- [X] T013 [P] Create TypeScript types in `frontend/src/types/auth.ts`: `Role` const enum (`admin`, `manager`, `sales_rep`, `support_agent`), `User` interface (id, email, role, display_name, active, locked, created_at), `AuthContextValue` interface
- [X] T014 [P] Create `AuthContext.tsx` skeleton: `AuthContext`, `AuthProvider` component with `user: User | null`, `isLoading: boolean`, stub `login()` and `logout()` methods — not yet wired to API in `frontend/src/context/AuthContext.tsx`
- [X] T015 [P] Create `useAuth.ts`: `useContext(AuthContext)` with null-guard throw if used outside `AuthProvider` in `frontend/src/hooks/useAuth.ts`
- [X] T016 [P] Create `get_current_user(request: Request) -> User` and `require_admin(user: User = Depends(get_current_user)) -> User` FastAPI dependencies — reads `request.state.user`, raises `HTTPException(401)` if not set, `HTTPException(403)` if not Admin in `backend/app/api/v1/dependencies.py`
- [X] T017 Create `auth.py` and `admin_users.py` router skeletons; register both under `/api/v1/auth` prefix in `backend/app/main.py`

**Checkpoint**: Foundation ready — ORM migration applied, PasswordHasher ready, all four user stories can proceed

---

## Phase 3: User Story 1 — Register a New User (Priority: P1) 🎯 MVP start

**Goal**: Admin calls `POST /api/v1/auth/users`; user record is created with bcrypt-hashed password and normalised email; created user can immediately log in (once US2 is complete); duplicate email returns 409; password < 8 chars returns 422.

**Independent Test**: `POST /api/v1/auth/users` with `{"email": "NEWREP@example.com", "password": "password1", "role": "sales_rep"}` → 201 with email stored as `newrep@example.com`; repeat with same email → 409; password `"short"` → 422; non-Admin caller → 403.

- [X] T018 [US1] Implement `SqliteUserRepository.create()` (inserts + returns User), `get_by_email()` (case-insensitive via `LOWER(email) = LOWER(:email)`), `get_by_id()`, `list_all()` in `backend/app/repositories/sqlite_user_repository.py`
- [X] T019 [US1] Implement `UserAdminService.create_user()`: lowercase-normalise email, call `get_by_email()` → raise 409 if found, validate `len(password) >= 8` → raise 422, validate role → raise 422, call `PasswordHasher.hash()`, call `repository.create()`, return `UserResponse` in `backend/app/services/user_admin_service.py`
- [X] T020 [US1] Implement `POST /api/v1/auth/users` handler: `require_admin` dependency, call `UserAdminService.create_user()`, return HTTP 201 `UserResponse` in `backend/app/api/v1/admin_users.py`
- [X] T021 [P] [US1] Write `backend/tests/integration/test_admin_users_api.py` user-creation cases: success (201, email normalised, bcrypt hash stored), duplicate email (409), short password (422), invalid role (422), non-Admin caller (403) — use seeded Admin session for Auth

**Checkpoint**: User Story 1 independently testable — Admin can create users via API (admin UI is Module 6)

---

## Phase 4: User Story 2 — Log In (Priority: P1)

**Goal**: User submits credentials → session created → `crm_session` cookie set (`HttpOnly; Secure; SameSite=Strict`) → redirect to dashboard; wrong password always returns generic 401 (same timing as real verify — dummy bcrypt run prevents enumeration); 5th consecutive failure locks account and subsequent requests return 401 even with correct password.

**Independent Test**: POST valid credentials → 200 + cookie set + redirect; POST wrong password → 401 `"Invalid username or password"` (no difference in body vs. unknown user); POST correct password after 5 failures → 401 (locked); rate-limit `POST /auth/login` to 20/min per IP.

- [X] T022 [US2] Implement `SessionService` with `create(user_id) -> Session` (UUID4 session_id, `expires_at = now + 30min`), `validate(session_id) -> Session | None` (check `last_active_at < NOW()-30min`), `touch(session_id)` (UPDATE `last_active_at`), `delete_by_id(session_id)`, `delete_by_user_id(user_id)` in `backend/app/services/session_service.py`
- [X] T023 [US2] Implement `AuthService.login()`: lowercase email, `get_by_email()` → `dummy_verify()` if not found (timing equalisation, research.md §5), else `PasswordHasher.verify()` → increment `FailedLoginAttempt` counter and check ≥ 5 → SET `user.locked=True` + raise 401; check `active=False` or `locked=True` → raise 401; success → reset failure counter + `SessionService.create()` in `backend/app/services/auth_service.py`
- [X] T024 [US2] Add rate-limit middleware for `POST /api/v1/auth/login` (20 req/min per source IP using `slowapi` or a custom `BaseHTTPMiddleware` counter) in `backend/app/middleware/rate_limit_middleware.py`; register in `backend/app/main.py`
- [X] T025 [US2] Implement `POST /api/v1/auth/login` handler: parse `LoginRequest`, call `AuthService.login()`, set `crm_session` cookie (`HttpOnly=True, secure=True, samesite="strict", max_age=1800`), return `{"user": UserResponse}` in `backend/app/api/v1/auth.py`
- [X] T026 [P] [US2] Implement `GET /api/v1/auth/me` handler: reads `request.state.user` (populated by SessionMiddleware, implemented in US3; returns 401 if absent), returns `MeResponse` in `backend/app/api/v1/auth.py`
- [X] T027 [P] [US2] Implement `AuthContext.tsx` fully: `useEffect` on mount calls `GET /api/v1/auth/me` → sets `user` (restores session) or `null` (no session); `login()` posts `LoginRequest` → sets `user`; `logout()` stubs `null` (POST wired in US3) in `frontend/src/context/AuthContext.tsx`
- [X] T028 [P] [US2] Create `LoginForm.tsx`: MUI `TextField` for email (RFC 5322 format validation) and password (min-length 8 shown as inline error before submit), `Button` with loading state, renders generic error banner on 401 (`"Invalid username or password"` — no field-specific wording), navigates to `/dashboard` on success in `frontend/src/components/auth/LoginForm.tsx`
- [X] T029 [P] [US2] Create `LoginPage.tsx`: centered MUI `Card` layout, renders `LoginForm`, route `/login` in `frontend/src/pages/LoginPage.tsx`
- [X] T030 [P] [US2] Write `backend/tests/integration/test_login_api.py`: valid credentials → 200 + cookie, wrong password → 401 same body, unknown user → 401 same body (no enumeration), inactive user → 401 same body, locked user → 401 same body, 5th failure locks account (SC-002), 6th correct attempt while locked → 401
- [X] T031 [P] [US2] Write `backend/tests/unit/test_auth_service.py`: login success path, lockout counter increments per failure, lockout triggered on 5th failure (SC-002), dummy_verify called when user not found, counter reset on successful login, session created on success
- [X] T032 [P] [US2] Write `backend/tests/unit/test_password_hasher.py`: `hash()` returns bcrypt string, `verify()` round-trip succeeds, `verify()` fails on wrong password, `dummy_verify()` completes without error (verifying bcrypt cost factor ≥ 12 from config)
- [X] T033 [P] [US2] Write `frontend/tests/LoginPage.test.tsx`: short password shows inline error before submit, email format error shows inline, generic 401 message displayed (no field hint), successful login calls navigate to `/dashboard`

**Checkpoint**: User Story 2 fully functional — login with lockout, dummy-bcrypt timing protection, and inline form validation independently testable

---

## Phase 5: User Story 3 — Log Out (Priority: P1)

**Goal**: Logged-in user clicks Logout → `POST /api/v1/auth/logout` → session deleted server-side → `crm_session` cookie cleared → redirect to `/login`; pressing back button shows login page (server-side invalidation); `SessionGuard` wraps all protected routes and redirects to `/login` on 401 (session expiry or no session); `SessionMiddleware` validates and touches session on every request.

**Independent Test**: Log in → click Logout → back button shows `/login` (not dashboard); `GET /api/v1/auth/me` with old cookie → 401; navigate to protected route with no cookie → redirect to `/login`.

- [X] T034 [US3] Implement `SessionMiddleware(BaseHTTPMiddleware)` in `backend/app/middleware/session_middleware.py`: read `crm_session` cookie, call `SessionService.validate(session_id)` → if `None` return `JSONResponse(401)` + `delete_cookie("crm_session")`; if valid set `request.state.user = session.user` + `asyncio.create_task(SessionService.touch(session_id))` (fire-and-forget per plan.md); pass-through unauthenticated requests to public routes
- [X] T035 [US3] Register `SessionMiddleware` in `backend/app/main.py` (before all route registrations); define `PUBLIC_PATHS = {"/api/v1/auth/login", "/api/v1/_test/..."}` that skip session validation
- [X] T036 [US3] Implement `POST /api/v1/auth/logout` handler: call `SessionService.delete_by_id(session_id)` from cookie, clear cookie (`Max-Age=0`), return 204 in `backend/app/api/v1/auth.py`
- [X] T037 [P] [US3] Create test helper endpoint `POST /api/v1/_test/sessions/expire?session_id=<sid>` that sets `last_active_at` to 31 minutes ago (enabled only when `ENVIRONMENT=test`); register in `backend/app/api/v1/test_helpers.py` and `backend/app/main.py`
- [X] T038 [P] [US3] Create `SessionGuard.tsx`: reads `useAuth().user` and `isLoading`; renders `CircularProgress` while loading; `<Navigate to="/login" replace />` if `user` is null; renders `children` otherwise in `frontend/src/components/auth/SessionGuard.tsx`
- [X] T039 [P] [US3] Create `RequireRole.tsx`: accepts `allowedRoles: Role[]` prop; reads `useAuth().user.role`; renders `<Navigate to="/access-denied" replace />` if role not in `allowedRoles`; renders `children` otherwise in `frontend/src/components/auth/RequireRole.tsx`
- [X] T040 [P] [US3] Create `AccessDeniedPage.tsx`: MUI layout with "Access Denied" heading and back-to-dashboard link in `frontend/src/pages/AccessDeniedPage.tsx`
- [X] T041 [P] [US3] Write `backend/tests/unit/test_session_middleware.py`: expired session returns 401 JSON + clears cookie, active session sets `request.state.user`, missing cookie passes through (no state set), `touch` is dispatched as background task on valid session
- [X] T042 [P] [US3] Write `frontend/tests/SessionGuard.test.tsx`: renders `children` when `user` is set, redirects to `/login` when `user` is null, renders `CircularProgress` while `isLoading` is true

**Checkpoint**: User Story 3 fully functional — logout, session expiry redirect, and protected-route guard independently testable

---

## Phase 6: User Story 4 — Admin Resets a User's Password (Priority: P2)

**Goal**: Admin calls `POST /auth/users/{id}/reset-password` → password updated + ALL existing sessions for that user invalidated immediately (SC-005); `POST .../deactivate` sets `active=False` + terminates sessions + guards against deactivating the last active Admin (409); `POST .../unlock` clears `locked` flag + resets `FailedLoginAttempt` counter.

**Independent Test**: Reset User A's password as Admin → HTTP 204 → User A's existing session returns 401 on next request → login with old password fails → login with new password succeeds (SC-005). Attempt to deactivate the only active Admin → 409.

- [X] T043 [US4] Implement `UserAdminService.reset_password(user_id, new_password)`: validate `len(new_password) >= 8` → 422, `get_by_id(user_id)` → 404 if not found, `PasswordHasher.hash(new_password)`, UPDATE `users.password_hash`, call `SessionService.delete_by_user_id(user_id)` (atomic invalidation per research.md §6) in `backend/app/services/user_admin_service.py`
- [X] T044 [US4] Implement `UserAdminService.deactivate_user(user_id)`: `get_by_id` → 404, count active Admins → raise 409 if this is the last active Admin (last-Admin guard), SET `user.active = False`, call `SessionService.delete_by_user_id(user_id)` in `backend/app/services/user_admin_service.py`
- [X] T045 [US4] Implement `UserAdminService.unlock_user(user_id)`: `get_by_id` → 404, SET `user.locked = False`, DELETE or zero-out `FailedLoginAttempt` row for `user.email` in `backend/app/services/user_admin_service.py`
- [X] T046 [US4] Implement `POST /api/v1/auth/users/{user_id}/reset-password` handler: `require_admin`, call `UserAdminService.reset_password()`, return 204 in `backend/app/api/v1/admin_users.py`
- [X] T047 [P] [US4] Implement `POST /api/v1/auth/users/{user_id}/deactivate` handler: `require_admin`, call `UserAdminService.deactivate_user()`, return 204 in `backend/app/api/v1/admin_users.py`
- [X] T048 [P] [US4] Implement `POST /api/v1/auth/users/{user_id}/unlock` handler: `require_admin`, call `UserAdminService.unlock_user()`, return 204 in `backend/app/api/v1/admin_users.py`
- [X] T049 [P] [US4] Extend `backend/tests/integration/test_admin_users_api.py` with US4 scenarios: reset-password invalidates all user sessions (SC-005), old password fails post-reset, new password succeeds, deactivate terminates session, last-Admin guard returns 409, unlock clears locked flag and resets failure counter

**Checkpoint**: User Story 4 fully functional — admin password reset, deactivation, and unlock with session invalidation independently testable

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Expired-session cleanup job and full quickstart validation

- [X] T050 Configure APScheduler 4.x `AsyncScheduler` hourly cleanup job `purge_expired_sessions` (`DELETE FROM sessions WHERE last_active_at < NOW()-30min`) in `backend/app/core/scheduler.py`; register in `backend/app/main.py` (consistent with modules 001–003 pattern)
- [X] T051 Run quickstart.md Scenarios 1–8 against local dev stack: successful login + cookie (SC-001), invalid credentials generic 401, lockout on 5th failure (SC-002), session expiry redirect (SC-003), logout + back-button guard, admin create user (SC-004), admin reset password (SC-005), deactivate + last-admin guard

**Checkpoint**: All 8 quickstart scenarios pass; SC-001–SC-005 validated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user stories**
  - T005→T006→T007→T008: strictly sequential (config → db engine → models → migration)
  - T009–T016: can start after T007 (schemas, repos, password hasher, seed, frontend types/context all independent)
  - T017: depends on T016 skeleton files existing
- **US1 (Phase 3)**: Starts after Phase 2 — adds SqliteUserRepository methods and UserAdminService.create_user()
- **US2 (Phase 4)**: Starts after Phase 2 — adds SessionService, AuthService.login(), rate-limit middleware, login/me endpoints, LoginForm, LoginPage
- **US3 (Phase 5)**: Starts after Phase 2 — adds SessionMiddleware, logout endpoint, SessionGuard, RequireRole; **T026 (GET /me) from US2 requires T034 (SessionMiddleware) to be wired before end-to-end tests pass**
- **US4 (Phase 6)**: Starts after Phase 2 — extends UserAdminService with reset/deactivate/unlock; depends on SessionService.delete_by_user_id() from US2 (T022)
- **Polish (Phase 7)**: Depends on US1–US4 complete

### User Story Dependencies

- **US1 (P1)**: Independent after Phase 2 — `UserAdminService.create_user()` only touches `users` table, no sessions needed
- **US2 (P1)**: Independent after Phase 2 — introduces `SessionService`; GET /me works fully only after US3's `SessionMiddleware` is registered
- **US3 (P1)**: Depends on US2's `SessionService` (T022) being implemented — `SessionMiddleware` calls `SessionService.validate()` and `touch()`
- **US4 (P2)**: Depends on US2's `SessionService.delete_by_user_id()` (T022) — password reset and deactivation delete user sessions

### Coordination Points

US3 (T034–T035) registers `SessionMiddleware` in `main.py`, which is also touched by US2's rate-limit middleware (T024) and Phase 2's router registration (T017). Coordinate merges on `backend/app/main.py` — each change adds a new `app.add_middleware()` or `app.include_router()` call, so merge conflicts are straightforward.

### Within Each User Story

- Backend: repository methods → service methods → route handler → integration tests
- Frontend (US2, US3): TypeScript types (Phase 2) → context implementation → component → page → frontend tests

### Parallel Opportunities

- T002, T003, T004 parallel with T001 (Phase 1)
- T009–T016 all parallel after T008 (all different files)
- Within US2: T026–T033 all parallel after T025 (different files — SessionService T022 → AuthService T023 → middleware T024 → handler T025 are sequential; then handler + frontend tests all parallel)
- Within US3: T037–T042 all parallel after T036
- Within US4: T047, T048, T049 parallel after T046
- US1 + US2 can work concurrently after Phase 2 (different files; US2 adds SessionService while US1 adds UserAdminService)
- US3 can start its frontend tasks (T038–T040) in parallel with US2's backend tasks

---

## Parallel Example: User Story 2

```bash
# Sequential: SessionService → AuthService → rate-limit → login handler
T022: session_service.py
T023: auth_service.py (depends on T022 SessionService.create())
T024: rate_limit_middleware.py (independent)
T025: POST /auth/login handler (depends on T023)

# All parallel after T025:
T026: GET /auth/me handler         — auth.py (same file, add new route)
T027: AuthContext.tsx              — context/AuthContext.tsx
T028: LoginForm.tsx                — components/auth/LoginForm.tsx
T029: LoginPage.tsx                — pages/LoginPage.tsx
T030: test_login_api.py           — tests/integration/
T031: test_auth_service.py        — tests/unit/
T032: test_password_hasher.py     — tests/unit/
T033: LoginPage.test.tsx          — frontend/tests/
```

---

## Parallel Example: Full Module (4 developers)

```bash
# After Phase 2 complete (T005-T017):
Dev A: US1 (T018-T021)  — UserAdminService + create user endpoint
Dev B: US2 (T022-T033)  — AuthService + SessionService + login flow
Dev C: US3 (T034-T042)  — SessionMiddleware + logout + SessionGuard
Dev D: US4 (T043-T049)  — reset-password + deactivate + unlock (needs Dev B's SessionService T022)

# Dev D must wait for Dev B's T022 (SessionService.delete_by_user_id) before starting T043/T044
# Dev C must wait for Dev B's T022 (SessionService.validate/touch) before starting T034
# All Devs coordinate on main.py (router + middleware registration)
```

---

## Implementation Strategy

### MVP First (User Story 2 Only — can log in)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (**CRITICAL** — ORM + migration + PasswordHasher)
3. Run seed.py to create initial Admin
4. Complete Phase 3: US1 — create test accounts via API
5. Complete Phase 4: US2 — login endpoint + LoginForm
6. **STOP and VALIDATE**: Quickstart Scenario 1 (login + dashboard redirect ≤ 2 s)
7. **STOP and VALIDATE**: Quickstart Scenario 2 (invalid credentials generic 401)
8. Complete Phase 5: US3 — session validation + logout
9. **VALIDATE**: Quickstart Scenarios 4, 5 (session expiry, logout)

### Incremental Delivery

1. Setup + Foundational → ORM ready, Admin seed works
2. US1 → Admin can create user accounts via API (CLI/curl)
3. US2 → Login with lockout protection + LoginForm UI
4. US3 → Logout + session expiry + protected routes
5. US4 → Admin password reset, deactivation, unlock
6. Polish → Session cleanup job + Scenarios 1–8 validation

### Parallel Team Strategy

US1 and US2 can be worked concurrently after Phase 2 (zero file conflicts — different service files, different route handlers). US3 blocks on US2's `SessionService` (T022); US4 blocks on US2's `SessionService.delete_by_user_id()` (T022). Coordinate one merge on `main.py` per new middleware/router registration.

---

## Notes

- `[P]` tasks touch different files and have no unresolved upstream dependency — safe to parallelize
- `[US#]` label maps each task to a specific user story for per-story progress tracking
- **Generic 401 for all login failures** (FR-006, research.md §5): same response body AND approximate time for wrong password, unknown user, locked account, inactive account — dummy bcrypt run equalises timing when user not found
- **`locked` and `active` are independent flags** (spec.md clarifications): `locked=True` prevents login regardless of `active`; `active=False` prevents login regardless of `locked`; Admin clears either independently (US4)
- **Last-Admin guard** (contracts/api.md): `POST .../deactivate` returns 409 if caller is the only active Admin — enforced in `UserAdminService.deactivate_user()` (T044)
- **Fire-and-forget `touch()`** in SessionMiddleware (plan.md post-design): `asyncio.create_task(touch(sid))` avoids adding DB write latency to every authenticated request
- **Session cleanup job** (data-model.md): hourly APScheduler job in Polish (T050) purges rows where `last_active_at < NOW()-30min` — middleware handles active-request expiry; job handles orphaned sessions
- **Seed script** (research.md §7): `python -m app.core.seed` is idempotent; credentials from env vars only — never hardcoded (Constitution IV)
- **Email normalisation** (spec.md FR-003): lowercase on every write and uniqueness check — enforced in `UserAdminService` and `SqliteUserRepository`, not only in the schema validator
- **Test endpoint** (quickstart.md Scenario 4): `POST /api/v1/_test/sessions/expire` gated by `ENVIRONMENT=test` — never exposed in production
- Constitution IV (Security First): parameterised queries only, `passlib` bcrypt cost 12, `HttpOnly` cookie, rate-limit on login — all checked in plan.md Constitution gate
