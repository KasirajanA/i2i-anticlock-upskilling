# Implementation Plan: User & Team Management

**Branch**: `006-user-team-management` | **Date**: 2026-06-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-user-team-management/spec.md`

---

## Summary

Extend the User entity (owned by Module 005) with profile fields (display name, avatar, timezone), implement role-based module access control with a code-defined permission matrix, allow users to change their own password, and give Admins the ability to create/manage named Teams with multi-member support and an optional designated lead. Backend: Python 3.14 + FastAPI (async) + SQLAlchemy 2.x/aiosqlite + Pillow. Frontend: React 18 + TypeScript + MUI v6.

---

## Technical Context

**Language/Version**: Python 3.14 (backend), TypeScript 5.x / Node 20+

**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy 2.x, aiosqlite, Pydantic v2, passlib[bcrypt], Pillow
- Frontend: React 18, MUI v6, React Router v6, TanStack Query v5, Vite, Vitest, RTL

**Storage**: SQLite — extends `users` table (additive migration); new `teams` and `team_members` tables

**Testing**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend)

**Target Platform**: Linux server (backend), modern browsers Chrome 120+, Firefox 121+, Safari 17+

**Project Type**: Web application — async REST API + React SPA

**Performance Goals**:
- SC-001: Admin creates user + assigns role ≤ 1 minute
- SC-002: Role change visible on next page reload (no logout)
- SC-003: Access denied response for all restricted modules (zero bypass)
- SC-004: Team creation with 20 members ≤ 30 s
- SC-005: User deactivation terminates session within 5 s

**Constraints**:
- No hard-delete of users (deactivation only)
- No custom roles or action-level permissions in v1
- Avatar stored locally in `storage/avatars/`; S3 deferred
- Role matrix is static code (not DB-driven)

**Scale/Scope**: ≤ 1,000 users; 4 fixed roles; ≤ 100 teams; ≤ 20 members per team

---

## Constitution Check

### Pre-Design Gate

| Principle | Status | Evidence |
|-----------|--------|---------|
| I. Coding Standards | ✅ PASS | PEP 8 + Ruff; TypeScript strict; ESLint Airbnb |
| II. SOLID | ✅ PASS | `UserProfileService`, `TeamService`, `AvatarProcessor`, `RoleGuard` — each single-responsibility; `IUserRepository` and `ITeamRepository` abstractions |
| III. DRY | ✅ PASS | `MODULE_PERMISSIONS` defined once, imported by backend `RoleGuard` and frontend `permissions.ts` |
| IV. Security First | ✅ PASS | MIME type + size validation on avatar; IANA tz validation via `zoneinfo`; no user can change their own role; last-Admin guard |
| V. UX | ✅ PASS | Role-restricted nav items hidden (not just disabled); `/access-denied` page with clear explanation; avatar upload shows progress + inline error |

**Constitution Check: PASS — proceed to Phase 1.**

### Post-Design Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| II. SOLID — O/C | ✅ PASS | New modules added to `MODULE_PERMISSIONS` dict; no existing service changes needed |
| III. DRY | ✅ PASS | Role change propagation logic lives only in `SessionMiddleware.dispatch()` |
| IV. Security | ✅ PASS | `AvatarProcessor` runs Pillow in `run_in_executor`; `active` flag checked in session middleware on every request |

---

## Project Structure

### Documentation (this feature)

```text
specs/006-user-team-management/
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
│   │   ├── auth.py                     # User ORM (extended with profile cols), Session, FailedLoginAttempt
│   │   └── team.py                     # Team, TeamMember ORM models
│   ├── schemas/
│   │   └── user_mgmt.py               # Pydantic v2: UserResponse, UpdateProfileRequest, TeamRequest
│   ├── repositories/
│   │   ├── sqlite_user_repository.py  # Existing; extended with team queries
│   │   └── sqlite_team_repository.py
│   ├── services/
│   │   ├── user_profile_service.py    # display_name, timezone, password-change
│   │   ├── team_service.py            # Create, add/remove members, lead constraint
│   │   └── avatar_processor.py        # MIME check, 2MB guard, Pillow resize to WEBP
│   ├── permissions.py                 # MODULE_PERMISSIONS dict (single source of truth)
│   ├── dependencies/
│   │   └── role_guard.py              # FastAPI Depends: check role vs. MODULE_PERMISSIONS
│   └── api/
│       └── v1/
│           ├── users.py               # GET/PATCH /users, /users/me, /users/me/avatar
│           ├── user_password.py       # POST /users/me/change-password
│           └── teams.py               # CRUD teams + member management
└── tests/
    ├── unit/
    │   ├── test_user_profile_service.py
    │   ├── test_avatar_processor.py
    │   ├── test_team_service.py
    │   └── test_role_guard.py
    └── integration/
        ├── test_users_api.py
        └── test_teams_api.py

frontend/
├── src/
│   ├── types/
│   │   └── user.ts                    # User, Team, Role enum, TeamMember
│   ├── permissions.ts                 # MODULE_PERMISSIONS (mirrors backend dict)
│   ├── services/
│   │   └── userApi.ts                 # Axios wrappers for all user/team endpoints
│   ├── hooks/
│   │   ├── useUsers.ts                # TanStack Query: user list + detail
│   │   └── useTeams.ts                # TanStack Query: team list + detail
│   ├── components/
│   │   └── users/
│   │       ├── UserRow.tsx            # Single user row in admin table
│   │       ├── RoleBadge.tsx          # MUI Chip coloured by role
│   │       ├── AvatarUpload.tsx       # Drag-drop/click-to-upload with preview
│   │       ├── TeamCard.tsx           # Team summary card (name, lead, count)
│   │       └── MemberPicker.tsx       # Multi-select autocomplete for team members
│   ├── guards/
│   │   ├── RequireRole.tsx            # Wraps routes; missing role → /access-denied
│   │   └── RequireAuth.tsx            # Wraps all protected routes (from Module 005)
│   └── pages/
│       ├── UserListPage.tsx           # Admin: full user management table
│       ├── ProfilePage.tsx            # Own profile: name, tz, avatar, password
│       ├── TeamListPage.tsx           # Admin: team management
│       └── AccessDeniedPage.tsx
└── tests/
    ├── UserListPage.test.tsx
    ├── ProfilePage.test.tsx
    ├── RequireRole.test.tsx
    └── TeamListPage.test.tsx
```

**Structure Decision**: Web application (Option 2) — consistent across all CRM modules.

---

## Key Design Decisions

### Role Guard (FastAPI Dependency)

```python
def require_module_access(module: str, write: bool = False):
    async def dependency(user: User = Depends(get_current_user)) -> User:
        allowed = MODULE_WRITE_PERMISSIONS[module] if write else MODULE_PERMISSIONS[module]
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="Access denied.")
        return user
    return dependency

# Usage in router:
@router.get("/deals", dependencies=[Depends(require_module_access("sales_pipeline"))])
```

### Active-Check in Session Middleware

```python
class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        session = await validate_and_touch(request)
        if session and not session.user.active:
            return JSONResponse({"detail": "Account deactivated."}, status_code=401)
        request.state.user = session.user if session else None
        return await call_next(request)
```

### Avatar Processor

```python
class AvatarProcessor:
    MAX_BYTES = 2 * 1024 * 1024  # 2 MB
    OUTPUT_SIZE = (200, 200)
    ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}

    async def process(self, upload: UploadFile, user_id: int) -> str:
        data = await upload.read()
        if len(data) > self.MAX_BYTES:
            raise HTTPException(413, "File exceeds 2 MB limit.")
        if upload.content_type not in self.ALLOWED_MIME:
            raise HTTPException(422, "Unsupported image format.")
        loop = asyncio.get_event_loop()
        path = await loop.run_in_executor(None, self._resize_and_save, data, user_id)
        return f"/static/avatars/{user_id}.webp"
```

### React RequireRole Guard

```typescript
const RequireRole: React.FC<{ module: string; write?: boolean; children: ReactNode }> = ({
  module, write = false, children,
}) => {
  const { user } = useAuth();
  const permissions = write ? MODULE_WRITE_PERMISSIONS[module] : MODULE_PERMISSIONS[module];
  if (!user || !permissions.includes(user.role)) {
    return <Navigate to="/access-denied" replace />;
  }
  return <>{children}</>;
};
```

---

## Complexity Tracking

> No constitution violations — table left empty intentionally.
