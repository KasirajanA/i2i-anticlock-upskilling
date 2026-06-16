# Quickstart Validation Guide: Customer Support (Module 003)

**Prerequisites**: Backend running on `http://localhost:8000`, frontend on `http://localhost:5173`. An Admin account seeded. Module 005 (Auth) and Module 006 (User Management) must be operational to create users.

---

## Setup

```bash
# Backend
cd backend && python -m uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev

# Run backend tests
cd backend && pytest tests/ -v

# Run frontend tests
cd frontend && npm test
```

---

## Scenario 1 — Create a Support Ticket (FR-001, SC-001)

**Goal**: Agent creates a ticket; it gets a unique ref ID and status `open`.

1. Log in as a Support Agent.
2. Navigate to **Support** → **New Ticket**.
3. Fill in Subject: `"Cannot log in"`, Priority: `High`, Contact: any existing contact.
4. Submit.

**Expected**:
- Ticket appears in the queue with ref `I2I-CRM-0001` (or next in sequence).
- Status badge shows `Open`.
- SLA countdown shows correct first-response window (4h for High).
- `GET /api/v1/support/tickets/1` returns ticket with `status: "open"` and `sla.first_response_due` ~4h from now.

---

## Scenario 2 — Ticket Lifecycle: Open → In Progress → Resolved → Closed (FR-003)

1. Open the ticket created in Scenario 1.
2. Click **Start Working** → status becomes `In Progress`. Confirm activity log entry.
3. Click **Add Reply**, enter `"We are investigating."`, uncheck Internal Note. Submit.
   - **Expected**: `sla.first_response_at` is set; SLA warning clears.
4. Click **Mark Resolved**. Confirm `resolved_at` in SLA record.
5. Click **Close Ticket**.
   - **Expected**: No further status buttons visible; Admin can still revert via API.

**Verify via API**:
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/support/tickets/1/activity
```
Expect 4 log entries: `creation`, `status_change` (×2), `reply_added`.

---

## Scenario 3 — SLA Breach Detection (FR-006, SC-002)

> Use the test endpoint to fast-forward time (available only in `ENVIRONMENT=test`).

1. Create a `Critical` priority ticket.
2. Call `POST /api/v1/_test/sla/advance-clock?minutes=65` to simulate 65 minutes passing.
3. Trigger the SLA check job: `POST /api/v1/_test/jobs/run-sla-check`.

**Expected**:
- Ticket shows `SLA Warning` / `SLA Breached` badge in the queue.
- Admin receives an in-app notification (check notification bell).
- `GET /api/v1/support/tickets/1/sla` returns `first_response_breached: true`.

---

## Scenario 4 — Customer Reply Re-opens a Resolved Ticket (FR-007, SC-004)

1. Resolve a ticket (Scenario 2, step 4).
2. As an agent, add a reply on the Resolved ticket.

**Expected**:
- Ticket status returns to `Open`.
- A new `SLARecord` is created (`cycle: 2`); original `SLARecord` has `is_active: false`.
- Assigned agent receives an in-app notification.
- Activity log shows `reopen` event.

---

## Scenario 5 — Queue Management & Assignment (FR-009)

1. Create two tickets — assign one to Agent A, leave one unassigned.
2. Log in as Agent A, navigate to **My Tickets**.
   - **Expected**: Only the assigned ticket appears.
3. Navigate to **Unassigned Queue**.
   - **Expected**: The unassigned ticket appears; Agent A can self-assign it.

---

## Scenario 6 — Inline Validation (FR-001)

1. Open New Ticket form.
2. Submit without filling Subject.
   - **Expected**: Inline error `"Subject is required"` appears; form does not submit.
3. Submit without selecting a Contact.
   - **Expected**: Inline error `"Contact is required"`.

---

## Scenario 7 — Ticket List Filtering (FR-010)

1. Create tickets with varied statuses and priorities.
2. Apply filter: Status = `In Progress`, Priority = `High`.
   - **Expected**: Only matching tickets displayed; count updates correctly.
3. Apply date range filter for today.
   - **Expected**: Results filtered to tickets created today.

---

## Unit Test Checklist

| Test File | Coverage |
|-----------|----------|
| `tests/unit/test_ticket_service.py` | Status transitions (valid + invalid), SLA record creation, re-open logic |
| `tests/unit/test_sla_engine.py` | SLA due-date calculation per priority, breach detection, warning threshold |
| `tests/unit/test_ticket_id_generator.py` | Sequential ID generation, formatting as `I2I-CRM-NNNN` |
| `tests/integration/test_tickets_api.py` | All CRUD endpoints, auth/role enforcement, pagination |
| `tests/integration/test_replies_api.py` | Reply creation, re-open trigger, internal note filtering |
| `frontend/tests/TicketQueue.test.tsx` | Queue rendering, filter controls, empty state |
| `frontend/tests/TicketDetail.test.tsx` | Status transitions, reply form, SLA display |
