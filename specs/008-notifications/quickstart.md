# Quickstart & Validation Guide: Notifications & Alerts (Module 008)

**Date**: 2026-06-16

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.14+ |
| Node.js | 20+ |
| SQLite | 3.x (bundled) |

---

## Project Setup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn[standard] sqlalchemy aiosqlite sse-starlette apscheduler pydantic pytest pytest-asyncio httpx
```

### Frontend

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install @mui/material @emotion/react @emotion/styled @mui/icons-material \
  @tanstack/react-query axios
npm install -D vitest @testing-library/react @testing-library/user-event jsdom
```

---

## Start the Development Stack

```bash
# Terminal 1 — backend
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

Frontend dev server: `http://localhost:5173`
API docs (Swagger): `http://localhost:8000/docs`

---

## Validation Scenarios

### SC-001 — Badge appears within 5 seconds

1. Open the app as User A (Sales Rep). Note: bell badge = 0.
2. In a second session (or via API), trigger an assignment event for User A:
   ```bash
   curl -X POST http://localhost:8000/api/v1/_test/emit \
     -H "Content-Type: application/json" \
     -d '{"user_id": 1, "event_type": "assignment", "title": "Deal DEAL-0001 assigned to you", "source_record_type": "deal", "source_record_id": 1}'
   ```
3. **Expected**: Bell badge increments to 1 within 5 seconds without page refresh.

---

### SC-002 — Pending notifications visible on login

1. Log out as User A.
2. Emit 3 notifications for User A via the test endpoint above.
3. Log back in as User A.
4. **Expected**: Bell badge shows 3; all 3 appear in the notification panel within 2 seconds.

---

### SC-003 — Preferences toggle works

1. Log in as User A.
2. Go to Notification Settings → disable "Comments".
3. Emit a `comment` event for User A.
4. **Expected**: Bell badge does NOT increment. Emit an `assignment` event — badge DOES increment.

---

### SC-004 — Digest fires for bulk > 10 notifications

1. Use the test endpoint to emit 15 `assignment` notifications for User A within 5 seconds:
   ```bash
   for i in $(seq 1 15); do
     curl -s -X POST http://localhost:8000/api/v1/_test/emit \
       -d "{\"user_id\": 1, \"event_type\": \"assignment\", \"title\": \"Bulk assign $i\", \"source_record_type\": \"deal\", \"source_record_id\": $i}" \
       -H "Content-Type: application/json"
   done
   ```
2. Wait 60 seconds for the APScheduler digest flush job.
3. Open the notification panel.
4. **Expected**: A single digest entry "15 deal assignments" instead of 15 individual items.

---

### SC-005 — 30-day purge job

1. Insert a notification with `expires_at` in the past:
   ```bash
   sqlite3 backend/crm.db "INSERT INTO notifications (user_id, event_type, title, expires_at, created_at) VALUES (1, 'assignment', 'Old notification', datetime('now', '-31 days'), datetime('now', '-31 days'));"
   ```
2. Manually trigger the purge job (or advance the test clock):
   ```bash
   curl -X POST http://localhost:8000/api/v1/_test/run-purge
   ```
3. **Expected**: The old notification no longer appears in the panel.

---

### Admin Rule — Role-targeted alert

1. Log in as Admin.
2. Create a rule:
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/notification-rules \
     -H "Authorization: Bearer <admin_token>" \
     -d '{"name": "High-value deal", "event_type": "deal_stage_change", "filter_field": "deal_value", "filter_operator": ">", "filter_value": "10000", "target_type": "role", "target_value": "Admin"}'
   ```
3. Emit a `deal_stage_change` event with `deal_value: 15000`.
4. Log in as another Admin user.
5. **Expected**: Admin user sees the notification even if they had `deal_stage_change` disabled in personal preferences.

---

## Running Tests

```bash
# Backend unit tests
cd backend && pytest tests/unit -v

# Backend integration tests (uses in-memory SQLite)
cd backend && pytest tests/integration -v

# Frontend component tests
cd frontend && npm run test

# Full test suite
cd backend && pytest && cd ../frontend && npm run test
```

---

## Key File References

| Artifact | Path |
|----------|------|
| Data model | `specs/008-notifications/data-model.md` |
| API contracts | `specs/008-notifications/contracts/api.md` |
| Backend entry | `backend/app/main.py` |
| SSE endpoint | `backend/app/api/v1/sse.py` |
| Rule engine | `backend/app/services/rule_engine.py` |
| Scheduler jobs | `backend/app/scheduler/jobs.py` |
| Notification bell | `frontend/src/components/notifications/NotificationBell.tsx` |
| SSE hook | `frontend/src/hooks/useEventSource.ts` |
| Settings page | `frontend/src/pages/NotificationSettingsPage.tsx` |
