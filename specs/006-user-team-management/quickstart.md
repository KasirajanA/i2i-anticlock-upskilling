# Quickstart Validation Guide: User & Team Management (Module 006)

**Prerequisites**: Backend running on `http://localhost:8000`, frontend on `http://localhost:5173`. Module 005 (Auth) operational. Admin account seeded.

---

## Setup

```bash
cd backend && python -m uvicorn app.main:app --reload
cd frontend && npm run dev

# Run tests
cd backend && pytest tests/users/ tests/teams/ -v
cd frontend && npm test -- --testPathPattern="(user|team)"
```

---

## Scenario 1 — Create a User and Assign a Role (FR-001, SC-001)

1. Log in as Admin.
2. Navigate to **Users → Add User**.
3. Enter email `newrep@example.com`, password `password1`, role `Sales Rep`, display name `New Rep`.
4. Submit.

**Expected**:
- User appears in the user list immediately.
- Logging in as `newrep@example.com` works.
- Sales Pipeline and Contacts visible; Customer Support **not** visible (role enforcement).
- Total time from form open to user ready: ≤ 1 minute.

---

## Scenario 2 — Role Change Takes Effect on Next Page Load (FR-005, SC-002)

1. Log in as Admin and as `newrep@example.com` (Sales Rep) in separate browser tabs.
2. Admin changes `newrep@example.com`'s role to `Support Agent`.
3. In the Sales Rep's tab, press F5 (page reload).

**Expected**:
- Sales Pipeline and Contract modules disappear from navigation.
- Customer Support module appears.
- No logout required — change visible after exactly one page reload.
- No error; session remains active.

---

## Scenario 3 — Role Restriction & Access Denied (FR-003, SC-003)

1. Log in as `newrep@example.com` (Support Agent after Scenario 2).
2. Directly navigate to `http://localhost:5173/sales`.

**Expected**: Redirect to `/access-denied` page immediately (no flicker of sales content).

3. Attempt `GET /api/v1/sales/deals` via curl with the Support Agent session.
   - **Expected**: HTTP 403 `{"detail": "Access denied."}`.

---

## Scenario 4 — Update Profile (Display Name, Timezone) (FR-006)

1. Log in as any user.
2. Navigate to **Profile → Edit Profile**.
3. Change display name to `Alice S.` and timezone to `Europe/London`.
4. Save.

**Expected**:
- New display name appears in the top navigation bar immediately (no reload).
- Date fields across the CRM render in London time.
- `GET /api/v1/users/me` returns updated `display_name` and `timezone`.

---

## Scenario 5 — Avatar Upload (FR-006)

1. On the Profile page, click **Upload Avatar**.
2. Select a valid 1.5 MB JPEG.

**Expected**: Avatar displays immediately; `/static/avatars/{user_id}.webp` returns the resized image.

3. Attempt to upload a 3 MB file.
   - **Expected**: Inline error `"File must be under 2 MB"` — no upload occurs.

4. Attempt to upload a `.txt` file.
   - **Expected**: Inline error `"Only image files are accepted"`.

---

## Scenario 6 — Change Own Password (FR-006)

1. On Profile, click **Change Password**.
2. Enter current password correctly; set new password `newpassword1`.
3. Submit.

**Expected**: HTTP 204; old password no longer works; new password works immediately.

4. Attempt with wrong current password.
   - **Expected**: Inline error `"Current password is incorrect"`.

---

## Scenario 7 — Create a Team and Assign Members (FR-007, FR-008)

1. Log in as Admin. Navigate to **Teams → Create Team**.
2. Name: `EMEA Sales`; add members (3 users); designate one as lead.
3. Submit.

**Expected**:
- Team appears in the team list with member count 3.
- `EMEA Sales` appears in assignment dropdowns across the CRM.
- The designated lead is suggested as default assignee for unowned team records.

---

## Scenario 8 — Last Admin Guard (FR-009)

1. Attempt to deactivate the only active Admin account.

**Expected**: HTTP 409 `"Cannot deactivate the last active administrator."` — request rejected.

---

## Scenario 9 — Deactivate User (FR-004, SC-005)

1. Admin deactivates a user who is currently logged in.

**Expected**:
- Deactivated user's session is terminated within 5 s (middleware checks `active` flag on next request).
- Deactivated user is redirected to the login page.
- Login with deactivated account returns 401.
- Their historical records (deals, tickets) remain visible to other users.

---

## Unit Test Checklist

| Test File | Coverage |
|-----------|----------|
| `tests/unit/test_user_profile_service.py` | Display name update, timezone validation, password change |
| `tests/unit/test_avatar_processor.py` | MIME validation, 2 MB limit, Pillow resize |
| `tests/unit/test_team_service.py` | Create, add/remove members, lead constraint, last-admin guard |
| `tests/unit/test_role_guard.py` | Module permission matrix, all 4 roles × all 6 modules |
| `tests/integration/test_users_api.py` | CRUD, role change, deactivation |
| `tests/integration/test_teams_api.py` | Create, member add/remove, lead assignment |
| `frontend/tests/UserListPage.test.tsx` | Admin-only render, role filter |
| `frontend/tests/ProfilePage.test.tsx` | Display name, timezone, avatar upload, password change |
| `frontend/tests/RequireRole.test.tsx` | Redirect to /access-denied for restricted routes |
