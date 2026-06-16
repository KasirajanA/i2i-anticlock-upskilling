# Tasks: User & Team Management (Module 006)

**Input**: Design documents from `specs/006-user-team-management/`

**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/api.md ✅ quickstart.md ✅

**Tests**: Not included — not requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks in same phase)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in every description

## Path Conventions

- Backend: `backend/app/`, `backend/alembic/`, `backend/tests/`
- Frontend: `frontend/src/`
- Storage: `storage/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add module-specific dependencies and static file serving before any feature work begins.

- [X] T001 Add Pillow≥10.x to backend/requirements.txt and pin exact version
- [X] T002 [P] Create storage/avatars/.gitkeep and add storage/avatars/*.webp entry to .gitignore
- [X] T003 [P] Mount FastAPI StaticFiles for /static/avatars → storage/avatars/ directory in backend/app/main.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema, ORM models, Pydantic schemas, permission matrix, and session middleware hardening — MUST be complete before any user story begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Create Alembic migration 006_user_team_management.py: ADD COLUMN display_name VARCHAR(100) NULLABLE, avatar_url VARCHAR(255) NULLABLE, timezone VARCHAR(64) DEFAULT 'UTC' to users table; CREATE TABLE teams (id, name UNIQUE NOT NULL, lead_user_id FK→users NULLABLE ON DELETE SET NULL, created_by_id FK→users, created_at, updated_at); CREATE TABLE team_members (team_id FK→teams, user_id FK→users, joined_at, PK(team_id, user_id)); add indexes (teams.name UNIQUE, team_members.user_id) in backend/alembic/versions/006_user_team_management.py
- [X] T005 [P] Add display_name (String(100), nullable), avatar_url (String(255), nullable), timezone (String(64), default='UTC', nullable) column mappings to the User SQLAlchemy ORM model in backend/app/models/auth.py
- [X] T006 [P] Create Team SQLAlchemy model (id, name, lead_user_id FK nullable, created_by_id FK, created_at, updated_at) and TeamMember model (team_id FK, user_id FK, joined_at, composite PK) with all relationship declarations in backend/app/models/team.py
- [X] T007 [P] Define all Pydantic v2 schemas: UserResponse, UserCreateRequest (email, password, role, display_name), UpdateProfileRequest (display_name, timezone), UpdateUserAdminRequest (role, active), ChangePasswordRequest (current_password, new_password), TeamCreateRequest (name, lead_user_id optional, member_ids), TeamUpdateRequest (name optional, lead_user_id optional), TeamResponse (id, name, lead summary, member_count, created_at), TeamDetailResponse (id, name, lead summary, members list, created_at), AddMembersRequest (user_ids) in backend/app/schemas/user_mgmt.py
- [X] T008 [P] Define MODULE_PERMISSIONS dict (6 modules → set of allowed role strings) and MODULE_WRITE_PERMISSIONS dict (5 writable modules → set of role strings with write access) matching the FR-002 role matrix exactly in backend/app/permissions.py
- [X] T009 [P] Mirror MODULE_PERMISSIONS and MODULE_WRITE_PERMISSIONS as TypeScript const objects with the same keys and role string values in frontend/src/permissions.ts
- [X] T010 [P] Define TypeScript types: Role union type (admin | manager | sales_rep | support_agent), User interface (id, email, display_name, role, active, locked, timezone, avatar_url, created_at), Team interface (id, name, lead summary, member_count, created_at), TeamDetail interface (id, name, lead summary, members array, created_at), TeamMember interface, PaginatedUsers, PaginatedTeams in frontend/src/types/user.ts
- [X] T011 [P] Create userApi.ts Axios service module: configure baseURL from env, enable withCredentials for crm_session cookie forwarding, export typed Axios instance in frontend/src/services/userApi.ts
- [ ] T012 Update SessionMiddleware.dispatch: after validate_and_touch, if session.user.active is False return JSONResponse({"detail": "Account deactivated."}, status_code=401); re-read users.role from DB on each request and overwrite request.state.user.role to propagate immediate role changes per research.md decision #5 in backend/app/middleware/session.py

**Checkpoint**: Foundation ready — all three user stories can now begin (in parallel if staffed, or sequentially in priority order).

---

## Phase 3: User Story 1 — Create & Manage Users (Priority: P1) 🎯 MVP

**Goal**: Admins can create users with a role, change roles, deactivate users; all module routes enforce the role matrix; deactivated users are rejected within 5 s.

**Independent Test**: Create a Support Agent user, log in as that user, verify Sales Pipeline route returns HTTP 403 and is absent from nav; deactivate that user and confirm their next API call returns 401.

### Implementation for User Story 1

- [X] T013 [P] [US1] Add list_users(role=None, active=None, q=None) → list[User], count_active_admins() → int, update_user_role(user_id, role) → User, and deactivate_user(user_id) → User async methods to backend/app/repositories/sqlite_user_repository.py
- [X] T014 [US1] Implement UserAdminService: create_user(email, password, role, display_name) → User (bcrypt hash, validates role enum), get_user(user_id) → User, list_users(role, active, q) → PaginatedUsers, update_role(admin_user, target_user_id, new_role) → User (raises HTTP 403 if admin_user.id == target_user_id), deactivate(admin_user, target_user_id) → User (calls count_active_admins(); raises HTTP 409 if count ≤ 1 before deactivation) in backend/app/services/user_admin_service.py
- [X] T015 [US1] Implement require_module_access(module: str, write: bool = False) factory returning a FastAPI Depends that raises HTTP 403 {"detail": "Access denied."} when request.state.user.role is not in MODULE_PERMISSIONS[module] (or MODULE_WRITE_PERMISSIONS[module] when write=True) in backend/app/dependencies/role_guard.py
- [X] T016 [P] [US1] Implement all admin user management endpoints: GET /api/v1/users (role/active/q query params, admin-only via require_module_access("user_team_management")), GET /api/v1/users/{user_id} (admin or own-user), POST /api/v1/users (create, admin-only), PATCH /api/v1/users/{user_id} (role + active, admin-only) in backend/app/api/v1/users.py
- [X] T017 [US1] Register users APIRouter with prefix=/api/v1 and tags=["users"] in backend/app/main.py
- [X] T018 [P] [US1] Add list_users(params), get_user(id), create_user(body), update_user(id, body) typed Axios functions to frontend/src/services/userApi.ts
- [X] T019 [P] [US1] Create useUsers TanStack Query hook: useUserList(filters: {role?, active?, q?}) with query key ["users", filters] and useUser(id) with query key ["users", id] in frontend/src/hooks/useUsers.ts
- [X] T020 [P] [US1] Implement RoleBadge MUI Chip component mapping role string to colour (admin→error, manager→warning, sales_rep→primary, support_agent→success) in frontend/src/components/users/RoleBadge.tsx
- [X] T021 [P] [US1] Implement UserRow component: MUI TableRow displaying email, display_name (fallback to email prefix), RoleBadge, active status chip, edit role MUI Select, and deactivate icon button in frontend/src/components/users/UserRow.tsx
- [X] T022 [P] [US1] Implement RequireRole guard: checks useAuth() user role against MODULE_PERMISSIONS[module]; redirects to /access-denied with state={module} if role not permitted; renders children otherwise in frontend/src/guards/RequireRole.tsx
- [X] T023 [P] [US1] Implement AccessDeniedPage: display module name from router state, show "You don't have access to {module}" message, and a "Go to Dashboard" MUI Button in frontend/src/pages/AccessDeniedPage.tsx
- [X] T024 [US1] Implement UserListPage: MUI Table with UserRow per user, role and active MUI Select filters at top, "Add User" MUI Button opening a create-user dialog form (email, password, role, display_name fields), confirm deactivation via MUI Dialog, invalidate ["users"] query on mutation in frontend/src/pages/UserListPage.tsx
- [X] T025 [US1] Add /users route wrapped in `<RequireRole module="user_team_management">` and /access-denied route (open to all authenticated users) to React Router config in frontend/src/App.tsx

**Checkpoint**: User Story 1 fully functional and independently testable — run quickstart.md Scenarios 1–3 and 8–9 to validate.

---

## Phase 4: User Story 2 — Manage Own Profile (Priority: P2)

**Goal**: Any logged-in user can update their display name, timezone, and avatar from their profile page, and change their password with current-password confirmation.

**Independent Test**: Log in as any user, update display name to "Test User" and timezone to "Europe/London", save — confirm GET /api/v1/users/me returns updated values and the name appears in the nav bar.

### Implementation for User Story 2

- [X] T026 [P] [US2] Implement AvatarProcessor service: async process(upload: UploadFile, user_id: int) → str validates content_type in {"image/jpeg","image/png","image/webp"} (raises HTTP 422), checks len(data) ≤ 2 MB (raises HTTP 413), runs Pillow Image.open → resize(200,200) → convert WEBP in asyncio.run_in_executor, writes to storage/avatars/{user_id}.webp, returns "/static/avatars/{user_id}.webp" in backend/app/services/avatar_processor.py
- [X] T027 [P] [US2] Implement UserProfileService: update_profile(user_id, display_name?, timezone?) → User (validates timezone via zoneinfo.available_timezones(), raises HTTP 422 if invalid; validates display_name 1–100 chars), change_password(user_id, current_password, new_password) → None (verify current with passlib.verify; raise HTTP 401 if wrong; bcrypt hash new; update DB) in backend/app/services/user_profile_service.py
- [X] T028 [P] [US2] Add GET /api/v1/users/me (returns own UserResponse), PATCH /api/v1/users/me (display_name + timezone only via UpdateProfileRequest), and POST /api/v1/users/me/avatar (multipart/form-data, delegates to AvatarProcessor, returns {avatar_url}) endpoints to backend/app/api/v1/users.py
- [X] T029 [P] [US2] Implement POST /api/v1/users/me/change-password endpoint: accept ChangePasswordRequest body, delegate to UserProfileService.change_password, return HTTP 204 on success in backend/app/api/v1/user_password.py
- [X] T030 [P] [US2] Register user_password APIRouter with prefix=/api/v1 and tags=["profile"] in backend/app/main.py
- [X] T031 [P] [US2] Add get_me(), update_me(body), upload_avatar(file: File), change_password(body) typed Axios functions to frontend/src/services/userApi.ts
- [X] T032 [P] [US2] Implement AvatarUpload component: MUI Box click/drag-drop zone, shows current avatar or placeholder, validates file.size ≤ 2 MB and file.type in allowed MIME set with inline MUI FormHelperText error before calling upload_avatar, shows MUI LinearProgress during upload in frontend/src/components/users/AvatarUpload.tsx
- [X] T033 [US2] Implement ProfilePage: MUI form with display_name TextField, timezone MUI Autocomplete backed by IANA tz list, AvatarUpload component, and separate "Change Password" MUI Accordion with current_password + new_password fields; invalidate ["users","me"] query on profile save in frontend/src/pages/ProfilePage.tsx
- [X] T034 [US2] Add /profile route (all authenticated users, wrapped in RequireAuth from Module 005) to React Router in frontend/src/App.tsx

**Checkpoint**: User Story 2 fully functional — run quickstart.md Scenarios 4–6 to validate.

---

## Phase 5: User Story 3 — Create & Manage Teams (Priority: P2)

**Goal**: Admins can create named teams, add/remove members, and designate a team lead; teams appear in assignment dropdowns across the CRM.

**Independent Test**: Create team "EMEA Sales" with 3 members, designate a lead, remove one member, confirm member count = 2 and lead remains if not removed; confirm team appears in GET /api/v1/teams.

### Implementation for User Story 3

- [X] T035 [P] [US3] Implement sqlite_team_repository with async methods: create_team(name, lead_user_id, member_ids, created_by_id) → Team, get_team(team_id) → TeamDetail, list_teams() → list[Team], update_team(team_id, name?, lead_user_id?) → Team, add_members(team_id, user_ids) → None (ignore duplicates), remove_member(team_id, user_id) → None (if removed user is lead, set lead_user_id=None), is_member(team_id, user_id) → bool in backend/app/repositories/sqlite_team_repository.py
- [X] T036 [US3] Implement TeamService: create_team(name, lead_user_id, member_ids, created_by) → Team (validates lead_user_id in member_ids if provided; raises HTTP 422 if not), update_team(team_id, name?, lead_user_id?) → Team (validates lead is member), add_members(team_id, user_ids) → None, remove_member(team_id, user_id) → None delegating to sqlite_team_repository in backend/app/services/team_service.py
- [X] T037 [P] [US3] Implement all team endpoints with require_module_access("user_team_management") guard: GET /api/v1/teams (→ PaginatedTeams), POST /api/v1/teams (→ 201 TeamDetail), GET /api/v1/teams/{team_id} (→ TeamDetail), PATCH /api/v1/teams/{team_id} (→ TeamDetail), POST /api/v1/teams/{team_id}/members (→ 204), DELETE /api/v1/teams/{team_id}/members/{user_id} (→ 204) in backend/app/api/v1/teams.py
- [X] T038 [US3] Register teams APIRouter with prefix=/api/v1 and tags=["teams"] in backend/app/main.py
- [X] T039 [P] [US3] Add list_teams(), create_team(body), get_team(id), update_team(id, body), add_members(id, body), remove_member(team_id, user_id) typed Axios functions to frontend/src/services/userApi.ts
- [X] T040 [P] [US3] Create useTeams TanStack Query hook: useTeamList() with query key ["teams"] and useTeam(id) with query key ["teams", id] in frontend/src/hooks/useTeams.ts
- [X] T041 [P] [US3] Implement TeamCard MUI Card component: title = team name, subtitle = lead display_name or "No lead assigned", footer = member count chip in frontend/src/components/users/TeamCard.tsx
- [X] T042 [P] [US3] Implement MemberPicker MUI Autocomplete (multiple=true) backed by useUserList() hook; renders selected users as MUI Chips showing display_name; supports search by display_name or email in frontend/src/components/users/MemberPicker.tsx
- [X] T043 [US3] Implement TeamListPage: MUI Grid of TeamCards, "Create Team" MUI Button opening a dialog with name TextField, MemberPicker, and lead MUI Select (options = selected members), edit team inline, remove member with MUI IconButton and confirmation; invalidate ["teams"] query on mutations in frontend/src/pages/TeamListPage.tsx
- [X] T044 [US3] Add /teams route wrapped in `<RequireRole module="user_team_management">` to React Router in frontend/src/App.tsx

**Checkpoint**: User Story 3 fully functional — run quickstart.md Scenario 7 to validate.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Apply the role guard to all existing module routers, run linting, and run the full quickstart validation suite.

- [ ] T045 [P] Apply require_module_access(module) Depends to all existing module APIRouters that don't yet have it per the FR-002 matrix: contacts router (all roles), sales pipeline router (admin/manager/sales_rep), contracts router (admin/manager/sales_rep), support router (admin/manager/support_agent), analytics router (all roles) in backend/app/api/v1/ respective router files
- [ ] T046 [P] Run Ruff linter (ruff check backend/app/) and fix all reported violations in all new backend/app/ files added in this module
- [ ] T047 [P] Run ESLint (npx eslint frontend/src/) and tsc --noEmit and fix all violations in all new frontend/src/ files added in this module
- [ ] T048 Run quickstart.md Scenarios 1–9 end-to-end against running dev servers and document any failures; ensure SC-001 (≤1 min to create user), SC-002 (role change on next reload), SC-003 (zero bypass), SC-004 (team creation ≤30 s), SC-005 (deactivation ≤5 s) are all met
- [ ] T049 [P] Verify role matrix completeness: manually exercise all 4 roles × 6 modules (24 combinations) against running backend and confirm HTTP 200/403 responses match MODULE_PERMISSIONS matrix exactly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all three user stories
- **User Stories (Phases 3–5)**: All depend on Foundational phase; can proceed in parallel across stories if team is staffed for it, or sequentially P1 → P2 → P2
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on US2 or US3 — independently testable after Phase 2
- **User Story 2 (P2)**: No dependency on US1 or US3 — independently testable after Phase 2 (profile endpoints are separate from admin endpoints)
- **User Story 3 (P2)**: Depends on US1 for MemberPicker (needs useUsers hook from T019); can still be implemented without US1 complete if useUsers is stubbed, but full integration requires T019

### Within Each User Story

- Repositories → Services → Endpoints (backend)
- API service functions → Query hooks → Leaf components → Page component → Router wiring (frontend)
- Models/schemas (Phase 2) before any service or endpoint work

---

## Parallel Execution Examples

### Phase 2 Parallel Block

```
T005  Extend User ORM (auth.py)
T006  Create Team/TeamMember ORM (team.py)
T007  Pydantic v2 schemas (user_mgmt.py)
T008  MODULE_PERMISSIONS backend dict (permissions.py)
T009  MODULE_PERMISSIONS frontend mirror (permissions.ts)
T010  TypeScript types (user.ts)
T011  userApi.ts Axios base (userApi.ts)
```

All seven can be written simultaneously — each is a different file.

### Phase 3 Parallel Block (after T014 + T015 complete)

```
T016  Admin user endpoints (users.py)
T018  userApi.ts admin functions
T019  useUsers hook
T020  RoleBadge component
T021  UserRow component
T022  RequireRole guard
T023  AccessDeniedPage
```

Seven tasks in parallel across seven different files.

### Phase 4 Parallel Block

```
T026  AvatarProcessor service (avatar_processor.py)
T027  UserProfileService (user_profile_service.py)
T028  /users/me endpoints (users.py)
T029  change-password endpoint (user_password.py)
T031  userApi.ts profile functions
T032  AvatarUpload component
```

Six tasks in parallel across six different files.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T012) — critical blocking phase
3. Complete Phase 3: User Story 1 (T013–T025)
4. **STOP and VALIDATE**: quickstart.md Scenarios 1–3, 8–9
5. Deploy/demo if ready — CRM is usable with role-enforced access control

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 complete → Role-enforced user management working (MVP)
3. US2 complete → Users can self-manage their profile
4. US3 complete → Teams operational across all CRM modules
5. Polish → Full validation of FR-002 role matrix; linting clean

### Parallel Team Strategy

With three developers after Phase 2 completes:
- **Dev A**: User Story 1 (T013–T025)
- **Dev B**: User Story 2 (T026–T034)
- **Dev C**: User Story 3 (T035–T044) — stub useUsers if US1 not yet merged

---

## Notes

- [P] = different file from all other [P] tasks in the same phase; safe to run concurrently
- [US1]/[US2]/[US3] = maps task to user story for traceability and independent delivery
- T004 (Alembic migration) must be the first committed DB change; run `alembic upgrade head` before testing any story
- T012 (session middleware) is in an existing Module 005 file — read the file before editing to avoid overwriting existing logic
- T028 adds to an existing Module 005-owned users.py; read current file state first
- storage/avatars/ must exist before the first avatar upload; T002 creates the .gitkeep placeholder
- Commit after each phase checkpoint to keep history bisectable
