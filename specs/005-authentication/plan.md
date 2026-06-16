# Implementation Plan: Authentication

**Branch**: `005-authentication` | **Date**: 2026-06-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-authentication/spec.md`

---

## Summary

Build a secure username/password authentication system for the CRM: Admin-created accounts with bcrypt-hashed passwords (cost 12), server-side session management (SQLite, `HttpOnly` cookie), 30-minute inactivity timeout, 5-failure account lockout, Admin-only password reset with immediate session invalidation, and user deactivation. Backend: Python 3.14 + FastAPI (async) + SQLAlchemy 2.x/aiosqlite + passlib. Frontend: React 18 + TypeScript + MUI v6.

---

## Technical Context

**Language/Version**: Python 3.14 (backend), TypeScript 5.x / Node 20+

**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy 2.x, aiosqlite, Pydantic v2, passlib[bcrypt]
- Frontend: React 18, MUI v6, React Router v6, TanStack Query v5, Vite, Vitest, RTL

**Storage**: SQLite via SQLAlchemy 2.x — `users`, `sessions`, `failed_login_attempts` tables

**Testing**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend)

**Target Platform**: Linux server (backend), modern browsers Chrome 120+, Firefox 121+, Safari 17+

**Project Type**: Web application — async REST API + React SPA

**Performance Goals**:
- SC-001: Login + dashboard redirect ≤ 2 s
- SC-003: Session expiry redirect ≤ 1 s
- SC-004: Admin creates new user in ≤ 1 min (UI flow)
- SC-005: Admin password reset effective immediately

**Constraints**:
- `HttpOnly; Secure; SameSite=Strict` cookie — no JWT, no localStorage token
- bcrypt cost factor exactly 12 (not configurable below this floor)
- MFA, SSO, RBAC out of scope v1
- Rate limit: `POST /auth/login` — 20 req/min per IP

**Scale/Scope**: ≤ 1,000 concurrent users; ≤ 4 roles; session expiry checked on every request via middleware

---

## Constitution Check

### Pre-Design Gate

| Principle | Status | Evidence |
|-----------|--------|---------|
| I. Coding Standards | ✅ PASS | PEP 8 + Ruff; TypeScript strict; ESLint Airbnb |
| II. SOLID | ✅ PASS | `AuthService`, `SessionService`, `UserAdminService`, `PasswordHasher` — each single-responsibility; `IUserRepository` abstraction; `SessionMiddleware` isolated from business logic |
| III. DRY | ✅ PASS | Generic 401 response assembled once in `AuthService._auth_failure()`; bcrypt run-in-executor wrapped once in `PasswordHasher` |
| IV. Security First | ✅ PASS | `HttpOnly` cookie; bcrypt cost 12; dummy bcrypt run prevents timing enumeration; rate limiter on login; parameterised queries |
| V. UX | ✅ PASS | Inline form validation (email format, password length); generic error message; hard-redirect on session expiry (acceptable v1 UX) |

**Constitution Check: PASS — proceed to Phase 1.**

### Post-Design Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| II. SOLID — S | ✅ PASS | `SessionMiddleware` only checks expiry + updates `last_active_at`; no auth logic |
| IV. Security | ✅ PASS | `last_active_at` update is a fire-and-forget background task to avoid adding latency to every request; session validity check is synchronous (fail-fast) |

---

## Project Structure

### Documentation (this feature)

```text
specs/005-authentication/
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
│   ├── core/
│   │   ├── config.py                   # Settings: SESSION_TIMEOUT_MINUTES=30, BCRYPT_ROUNDS=12
│   │   ├── database.py                 # Async engine, session factory
│   │   └── seed.py                     # Idempotent Admin seed from env vars
│   ├── models/
│   │   └── auth.py                     # ORM: User, Session, FailedLoginAttempt
│   ├── schemas/
│   │   └── auth.py                     # Pydantic v2: LoginRequest, UserResponse, CreateUserRequest
│   ├── repositories/
│   │   ├── base.py                     # IUserRepository (abstract)
│   │   └── sqlite_user_repository.py
│   ├── services/
│   │   ├── auth_service.py             # Login, logout, lockout, dummy-bcrypt
│   │   ├── session_service.py          # Create, validate, delete sessions
│   │   ├── user_admin_service.py       # Admin CRUD: create, reset-password, deactivate, unlock
│   │   └── password_hasher.py          # bcrypt hash/verify (run_in_executor)
│   ├── middleware/
│   │   └── session_middleware.py       # Starlette middleware: validate + touch last_active_at
│   └── api/
│       └── v1/
│           ├── auth.py                 # /login, /logout, /me
│           └── admin_users.py          # /users, /users/{id}/reset-password, etc.
└── tests/
    ├── unit/
    │   ├── test_auth_service.py
    │   ├── test_password_hasher.py
    │   └── test_session_middleware.py
    └── integration/
        ├── test_login_api.py
        └── test_admin_users_api.py

frontend/
├── src/
│   ├── types/
│   │   └── auth.ts                     # User, Role enum, AuthContext type
│   ├── context/
│   │   └── AuthContext.tsx             # React context: currentUser, login(), logout()
│   ├── hooks/
│   │   └── useAuth.ts                  # useContext(AuthContext) with null-guard
│   ├── components/
│   │   └── auth/
│   │       ├── LoginForm.tsx           # MUI TextField + Button, inline validation
│   │       ├── SessionGuard.tsx        # Wraps protected routes; 401 → redirect to /login
│   │       └── RequireRole.tsx         # Wraps role-restricted pages; 403 → /access-denied
│   └── pages/
│       ├── LoginPage.tsx
│       └── AccessDeniedPage.tsx
└── tests/
    ├── LoginPage.test.tsx
    └── SessionGuard.test.tsx
```

**Structure Decision**: Web application (Option 2) — consistent with Module 008, 003, and 004.

---

## Key Design Decisions

### Password Hasher (async-safe bcrypt)

```python
class PasswordHasher:
    def __init__(self, rounds: int = 12):
        self._context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=rounds)

    async def hash(self, password: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._context.hash, password)

    async def verify(self, password: str, hashed: str) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._context.verify, password, hashed)

    async def dummy_verify(self) -> None:
        """Run a bcrypt verify to equalise timing when user not found."""
        await self.verify("_dummy_", "$2b$12$OJ2T7pALKe5j3rPJl5ZrxO...")
```

### Session Middleware

```python
class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get("crm_session")
        if session_id:
            session = await self._session_service.validate(session_id)
            if session is None:
                response = JSONResponse({"detail": "Session expired."}, status_code=401)
                response.delete_cookie("crm_session")
                return response
            request.state.user = session.user
            asyncio.create_task(self._session_service.touch(session_id))  # fire-and-forget
        return await call_next(request)
```

### React Auth Context

```typescript
interface AuthContextValue {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isLoading: boolean;
}

// SessionGuard.tsx
const SessionGuard: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  if (isLoading) return <CircularProgress />;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
};
```

---

## Complexity Tracking

> No constitution violations — table left empty intentionally.
