# Research: Authentication (Module 005)

**Date**: 2026-06-16 | **Feature**: 005-authentication

---

## 1. Password Hashing

**Decision**: `bcrypt` via the `passlib[bcrypt]` library, cost factor 12.

**Rationale**: FR-002 mandates bcrypt with cost factor ≥ 12. `passlib` provides a stable, well-audited async-compatible wrapper. Cost 12 is the industry standard baseline (≈ 250 ms on modern hardware — resistant to brute-force, acceptable for interactive login). Verification is CPU-bound; it runs in `asyncio.get_event_loop().run_in_executor(None, ...)` to avoid blocking the FastAPI event loop.

**Alternatives considered**: `argon2-cffi` (superior algorithm but not explicitly required by spec); `hashlib.sha256` (forbidden by FR-002); `bcrypt` directly (works, `passlib` adds hash format versioning).

---

## 2. Session Storage

**Decision**: Server-side session table (`sessions`) in SQLite; client holds an opaque `session_id` in an `HttpOnly; Secure; SameSite=Strict` cookie.

**Rationale**: FR-008 specifies server-side session invalidation; the session token must be revokable without client cooperation (logout, admin password reset, deactivation). An `HttpOnly` cookie prevents JavaScript XSS from stealing the token. `SameSite=Strict` mitigates CSRF. The `sessions` table stores `session_id` (UUID4), `user_id`, `created_at`, `last_active_at`, and `expires_at`. A background job purges expired sessions.

**Alternatives considered**: JWT (stateless, not revokable without blocklist — violates FR-009/FR-010); `localStorage` token (accessible to JS, XSS risk); Redis session store (external dependency, out of scope).

---

## 3. Session Expiry (30-minute Inactivity)

**Decision**: `last_active_at` updated on every authenticated request via FastAPI middleware. Session is considered expired when `NOW() - last_active_at > 30 minutes`. Middleware returns HTTP 401 on expiry; frontend hard-redirects to `/login`.

**Rationale**: FR-008 specifies 30-minute inactivity timeout. Updating `last_active_at` on every request is a single `UPDATE sessions SET last_active_at=NOW() WHERE session_id=:sid` — cheap for SQLite at ≤ 1,000 concurrent users. The frontend receives 401 and redirects unconditionally (no modal, per spec).

**Alternatives considered**: Fixed absolute expiry (no activity extension); JWT with short TTL + refresh token (two-token complexity, still not truly server-revocable for mid-session admin resets).

---

## 4. Account Lockout

**Decision**: `FailedLoginAttempt` table with per-username counter + timestamp; counter reset on successful login. After 5 failures the `users.locked` boolean is set; only an Admin can clear it.

**Rationale**: FR-007 requires lockout after 5 consecutive failures. Storing attempts in the DB (not in-memory) ensures lock survives server restarts and is consistent across hypothetical future replicas. The failure counter uses the normalised email (lowercase) as the key to prevent bypass via email case variation.

**Alternatives considered**: In-memory counter (lost on restart, inconsistent); rate-limiting middleware without DB persistence (doesn't distinguish per-account from per-IP); token bucket (over-engineered for this use case).

---

## 5. Generic Error Messages (No Account Enumeration)

**Decision**: `POST /auth/login` always returns `HTTP 401 {"detail": "Invalid username or password"}` regardless of whether the username exists or the password is wrong.

**Rationale**: FR-006 prohibits account enumeration. The same response and timing must be returned for "user not found" and "wrong password". To prevent timing side-channels, a dummy bcrypt verify is run when the user is not found (so response time ≈ same as a real bcrypt check).

**Alternatives considered**: Different HTTP status codes for different failures (explicit enumeration risk); constant-time sleep (less reliable than real bcrypt computation).

---

## 6. Admin Password Reset — Session Invalidation

**Decision**: `POST /auth/users/{user_id}/reset-password` (Admin only): update `users.password_hash`, then `DELETE FROM sessions WHERE user_id = :user_id`.

**Rationale**: FR-010 requires all existing sessions for the target user to be invalidated immediately on password reset. Deleting all session rows for the user is atomic in SQLite and simpler than maintaining a token blocklist.

**Alternatives considered**: Setting a `invalidated_at` column on User and checking it in middleware (adds a DB read to every request); JWT rotation (stateless, can't invalidate without blocklist).

---

## 7. Seed Admin Account

**Decision**: A seed script (`python -m app.core.seed`) creates the initial Admin account if none exists. The email and password are read from environment variables (`SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`).

**Rationale**: FR-001 requires a single Admin to be seeded at setup. Using env vars keeps credentials out of source code (Constitution IV). The seed script is idempotent — running it twice does not create duplicate accounts.

**Alternatives considered**: Hardcoded default credentials in code (violates Constitution IV); interactive CLI prompt (inconvenient in Docker/CI environments).
