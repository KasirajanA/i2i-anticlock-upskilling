# Quickstart: Contract Management

## Prerequisites

| Requirement       | Version / Notes                                          |
|-------------------|----------------------------------------------------------|
| Python            | 3.14+                                                    |
| pip / venv        | Bundled with Python                                      |
| Node.js           | 20 LTS+                                                  |
| npm               | 10+                                                      |
| SQLite            | 3.35+ (WAL mode support; ships with Python)              |
| Git               | Any recent version                                       |
| curl              | For manual API validation steps below                    |

---

## Backend Setup

```bash
# 1. Create and activate a virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialise the database (runs Alembic migrations)
alembic upgrade head

# 4. Start the development server
uvicorn app.main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

---

## Frontend Setup

```bash
# From a separate terminal
cd frontend
npm install
npm run dev
```

The React app is now available at `http://localhost:5173`.

---

## Validation Scenarios (by Success Criterion)

### SC-001: Create a contract in under 2 minutes

**Browser steps**:
1. Log in as a Sales Rep user.
2. Navigate to **Contracts → New Contract**.
3. Fill in: account (select existing), value `5000`, start date `2026-07-01`, end date `2026-12-31`.
4. Click **Save**. Verify the contract appears in the list with status `Draft` and a `CON-NNNN` reference ID within the same page load.

**curl equivalent** (obtain `SESSION` cookie from login first):
```bash
curl -s -X POST http://localhost:8000/api/v1/contracts \
  -H "Content-Type: application/json" \
  -b "session_id=$SESSION" \
  -d '{"value": 5000, "start_date": "2026-07-01", "end_date": "2026-12-31", "account_id": 1}' \
  | python -m json.tool
# Expect: HTTP 201, "status": "Draft", "ref_id": "CON-NNNN"
```

---

### SC-002: Auto-expiry runs within 24 hours

**Setup**: Create a contract with `end_date` = yesterday. Trigger the scheduler job manually:
```bash
curl -s -X POST http://localhost:8000/api/v1/internal/jobs/expire-contracts \
  -b "session_id=$SESSION"
# (Admin session required)
```
Then verify:
```bash
curl -s http://localhost:8000/api/v1/contracts/CON-0001 \
  -b "session_id=$SESSION" | python -m json.tool
# Expect: "status": "Expired"
```

---

### SC-003: Renewal Due flag within 24 hours of entering the 30-day window

**Setup**: Create a contract with `end_date` = today + 25 days and status `Active`. Trigger the renewal job:
```bash
curl -s -X POST http://localhost:8000/api/v1/internal/jobs/flag-renewals \
  -b "session_id=$SESSION"
```
Then check:
```bash
curl -s http://localhost:8000/api/v1/contracts/CON-0002 \
  -b "session_id=$SESSION" | python -m json.tool
# Expect: "is_renewal_due": true
```
Log in to the web app as the contract owner and confirm the in-app notification badge shows.

---

### SC-004: Filtered list returns in under 1 second for 10k records

**Setup**: Seed 10,000 contracts via the test fixture script:
```bash
cd backend
python scripts/seed_contracts.py --count 10000
```
Then time a filtered query:
```bash
time curl -s "http://localhost:8000/api/v1/contracts?status=Active&limit=20" \
  -b "session_id=$SESSION" > /dev/null
# Expect: real time < 1.0s
```

---

### SC-005: Renewal pre-fill copies all required fields accurately

```bash
# Renew an existing Active contract
curl -s -X POST http://localhost:8000/api/v1/contracts/CON-0001/renew \
  -b "session_id=$SESSION" | python -m json.tool
# Expect: successor.account_id, value, description match originals
# Expect: successor start_date = original end_date + 1 day
# Expect: HTTP 201
```

---

### SC-006: File upload under 2 seconds for a 1 MB file

```bash
# Generate a 1 MB test file
dd if=/dev/urandom of=/tmp/test_attachment.pdf bs=1024 count=1024

time curl -s -X POST http://localhost:8000/api/v1/contracts/CON-0001/attachment \
  -b "session_id=$SESSION" \
  -F "file=@/tmp/test_attachment.pdf;type=application/pdf"
# Expect: HTTP 201, real time < 2.0s
```

---

## Running Tests

### Backend

```bash
cd backend
source .venv/bin/activate

# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# With coverage report
pytest --cov=app --cov-report=term-missing
```

### Frontend

```bash
cd frontend

# All tests (watch mode)
npm run test

# Single run with coverage
npm run test -- --run --coverage
```

### Linting

```bash
# Backend
cd backend && ruff check app/ tests/

# Frontend
cd frontend && npm run lint
```
