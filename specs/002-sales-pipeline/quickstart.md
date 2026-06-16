# Quickstart: Sales Pipeline

**Module**: 002 - Sales Pipeline
**Date**: 2026-06-16

---

## Prerequisites

| Requirement       | Version  | Check Command                     |
|-------------------|----------|-----------------------------------|
| Python            | 3.14+    | `python --version`                |
| pip               | 24+      | `pip --version`                   |
| Node.js           | 20 LTS+  | `node --version`                  |
| npm               | 10+      | `npm --version`                   |
| SQLite            | 3.35+    | `sqlite3 --version`               |
| Git               | 2.40+    | `git --version`                   |

---

## Backend Setup

```bash
# 1. Enter the backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment config
cp .env.example .env
# Edit .env if needed — defaults work for local SQLite

# 5. Run database migrations (creates/updates crm.db)
alembic upgrade head

# 6. Start the development server
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

---

## Frontend Setup

```bash
# 1. Enter the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Copy environment config
cp .env.example .env.local
# VITE_API_BASE_URL=http://localhost:8000  (default)

# 4. Start the development server
npm run dev
```

The app is available at `http://localhost:5173`.

---

## Validation Scenarios

### SC-001: Pipeline view loads in under 2 seconds for 500 deals

**Scenario**: Seed 500 deals and confirm the board renders within 2 seconds.

```bash
# Seed 500 deals via the seed script
cd backend
python -m app.scripts.seed --deals 500

# Then open the browser at http://localhost:5173/pipeline
# and observe the Network tab — the GET /api/v1/deals request
# should complete in under 500ms (well within the 2s page budget).
```

Alternatively, use curl with timing:

```bash
curl -s -o /dev/null -w "Time: %{time_total}s\n" \
  -b "session_id=<your_session_cookie>" \
  "http://localhost:8000/api/v1/deals?limit=100&page=1"
```

Expected: response time under 500ms (API p95 target ≤ 200ms).

---

### SC-002: Stage change is logged immediately

**Scenario**: Move a deal to a new stage and confirm the activity log entry appears without page refresh.

```bash
# Step 1 — Create a deal
curl -s -X POST http://localhost:8000/api/v1/deals \
  -H "Content-Type: application/json" \
  -b "session_id=<your_session_cookie>" \
  -d '{"title":"Test Deal","value":5000,"stage":"Lead In","expected_close_date":"2026-09-30","owner_id":1,"account_id":1}' \
  | jq '.ref_id'
# Note the ref_id, e.g., "DEAL-0001"

# Step 2 — Advance the stage
curl -s -X POST http://localhost:8000/api/v1/deals/DEAL-0001/stage \
  -H "Content-Type: application/json" \
  -b "session_id=<your_session_cookie>" \
  -d '{"stage":"Qualified"}'

# Step 3 — Confirm activity log entry
curl -s http://localhost:8000/api/v1/deals/DEAL-0001/activity \
  -b "session_id=<your_session_cookie>" \
  | jq '.items[] | select(.action_type=="stage_changed")'
```

Expected: one `stage_changed` entry with `note: "Lead In → Qualified"` and a current timestamp.

---

### SC-003: Forecast totals are accurate to source records

**Scenario**: Create deals with known values in each stage and verify the forecast endpoint returns exact totals.

```bash
# Create one deal in each non-closed stage with known values
# Lead In: 10000, Qualified: 20000, Proposal: 30000, Negotiation: 40000

# Fetch forecast for the same period
curl -s "http://localhost:8000/api/v1/pipeline/forecast?period=2026-07-01/2026-09-30" \
  -b "session_id=<manager_session_cookie>" \
  | jq '.open_pipeline[] | {stage: .stage, total_value: .total_value, weighted_value: .weighted_value}'
```

Expected values:

| Stage       | total_value | probability | weighted_value |
|-------------|-------------|-------------|----------------|
| Lead In     | 10000.00    | 0.10        | 1000.00        |
| Qualified   | 20000.00    | 0.25        | 5000.00        |
| Proposal    | 30000.00    | 0.50        | 15000.00       |
| Negotiation | 40000.00    | 0.75        | 30000.00       |

`total_weighted_forecast` = 51000.00

---

## Running Tests

### Backend

```bash
cd backend
source .venv/bin/activate

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run only pipeline module tests
pytest tests/ -k "pipeline or deal"

# Run integration tests only
pytest tests/integration/
```

### Frontend

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode during development
npm run test:watch

# Run with coverage
npm run test:coverage

# Run only pipeline-related tests
npm test -- --testPathPattern="pipeline|deal"
```

### Full suite (both backend and frontend)

```bash
# From repo root
cd backend && pytest && cd ../frontend && npm test
```
