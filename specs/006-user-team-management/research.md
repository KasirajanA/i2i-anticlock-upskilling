# Research: User & Team Management (Module 006)

**Date**: 2026-06-16 | **Feature**: 006-user-team-management

---

## 1. Shared User Table Strategy

**Decision**: Single `users` table shared by Module 005 (Auth) and Module 006 (User Mgmt). Module 005 owns `email`, `password_hash`, `role`, `active`, `locked`. Module 006 adds `display_name`, `avatar_url`, `timezone` columns via a migration in this module.

**Rationale**: Spec clarification confirms one User table. Keeping a single ORM model avoids JOIN complexity and data drift. The migration is additive (nullable columns with defaults) so it does not break Module 005's existing operations. Both modules import the same `User` ORM model; responsibility boundary is maintained through separate services (`AuthService` vs `UserProfileService`).

**Alternatives considered**: Separate `user_profiles` table with 1:1 FK (clean boundary but adds JOIN on every profile read); denormalised duplication (violates DRY, drift risk).

---

## 2. Role-Based Navigation Guard

**Decision**: Role matrix implemented in two places: (1) backend `RoleGuard` dependency raises HTTP 403 for protected routes; (2) frontend `RequireRole` component redirects to `/access-denied` before rendering.

**Rationale**: Defense-in-depth (FR-003): API enforces access; UI hides navigation items. The role matrix is defined once as a `MODULE_PERMISSIONS` dict in a shared `permissions.py` module imported by both the `RoleGuard` dependency and the frontend permissions config (`permissions.ts`). Adding a new module requires editing only that one dict.

**Alternatives considered**: Database-driven permissions table (over-engineered for 4 fixed roles; adds query per request); middleware-only enforcement (harder to test unit-level; still needs frontend hiding).

---

## 3. Avatar Upload

**Decision**: `POST /api/v1/users/me/avatar` accepts multipart/form-data; backend validates MIME type (JPEG, PNG, WEBP), max size 2 MB, resizes to 200×200 px using `Pillow` in `run_in_executor`, stores as local file in `storage/avatars/{user_id}.webp`. URL served as `/static/avatars/{user_id}.webp`.

**Rationale**: Spec limits avatar to 2 MB (FR-006). Pillow resizing normalises dimensions and converts to WEBP for efficient serving. `run_in_executor` keeps Pillow's CPU-bound operation off the event loop. `storage/` directory is gitignored; in production this would be an S3 bucket (deferred). MIME type validation prevents polyglot file attacks.

**Alternatives considered**: Base64-encode avatar in DB (no separate file serving needed, but bloats DB and makes binary updates expensive); S3 directly (external dependency, out of scope MVP).

---

## 4. Team Membership (Many-to-Many)

**Decision**: `team_members` join table with `(team_id, user_id)` composite PK; `teams.lead_user_id` nullable FK for the designated team lead.

**Rationale**: FR-010 allows a user to belong to multiple teams. A join table is the standard normalised approach. The team lead is a single user (not a role), stored as a column on `teams` for query simplicity. When the lead is removed from the team, `lead_user_id` is nulled automatically via `ON DELETE SET NULL`.

**Alternatives considered**: JSON array of user IDs in `teams` (not relational, hard to join); separate `team_leads` table (unnecessary for one lead per team).

---

## 5. Role Change — Immediate Effect on Next Page Load

**Decision**: Role is stored in the server-side `sessions` table row (denormalised into `sessions.role_snapshot`). On each request, the session middleware re-reads `users.role` from the DB and compares to `sessions.role_snapshot`. If different, it updates `sessions.role_snapshot` and injects the fresh role into `request.state.user`.

**Rationale**: FR-005 requires the role change to take effect on the user's next page load — no logout required. Since the session is server-side, the middleware can always return the current role from `users` rather than the stale cached value. No client-side cache invalidation needed.

**Alternatives considered**: Invalidate all sessions on role change (forces re-login — violates spec); include role in JWT (stateless, requires token re-issue to propagate changes).

---

## 6. Last Admin Guard

**Decision**: Before deactivating a user, `UserAdminService.deactivate()` counts `SELECT COUNT(*) FROM users WHERE role='admin' AND active=TRUE`. If count ≤ 1, raise HTTP 409.

**Rationale**: FR-009 requires preventing deactivation of the last active Admin. The guard runs inside the same DB transaction as the deactivate update so it is race-condition safe in SQLite (WAL serialises writes).

**Alternatives considered**: Application-level lock (not needed; SQLite write serialisation is sufficient); trigger (not async-compatible).

---

## 7. Timezone Handling

**Decision**: User's `timezone` stored as an IANA timezone string (e.g., `"America/New_York"`). Validated on write by checking against `zoneinfo.available_timezones()`. Used by the frontend (`date-fns-tz`) for all date/time rendering. Not used server-side (all DB datetimes are UTC).

**Rationale**: Frontend-only TZ conversion is the standard approach (see Module 004 research). The `zoneinfo` module (Python 3.9+ stdlib) validates the IANA identifier without external dependencies.

**Alternatives considered**: UTC offset integer (doesn't handle DST); pytz (deprecated in favour of `zoneinfo`).
