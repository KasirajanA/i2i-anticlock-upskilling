"""T045: Integration tests — full CRUD, transitions, attachments, activity log."""

import io
import pytest
from datetime import date


BASE = "/api/v1/contracts"


@pytest.mark.asyncio
async def test_create_contract(client, test_account):
    resp = await client.post(BASE, json={
        "value": 5000.0,
        "start_date": "2026-07-01",
        "end_date": "2026-12-31",
        "account_id": test_account.id,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "Draft"
    assert data["ref_id"].startswith("CON-")


@pytest.mark.asyncio
async def test_create_contract_invalid_dates(client, test_account):
    resp = await client.post(BASE, json={
        "value": 5000.0,
        "start_date": "2026-12-31",
        "end_date": "2026-01-01",
        "account_id": test_account.id,
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_contract_unknown_account(client):
    resp = await client.post(BASE, json={
        "value": 5000.0,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "account_id": 9999,
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_contract(client, test_account):
    create = await client.post(BASE, json={
        "value": 1000.0,
        "start_date": "2026-01-01",
        "end_date": "2026-06-30",
        "account_id": test_account.id,
    })
    ref_id = create.json()["ref_id"]

    resp = await client.get(f"{BASE}/{ref_id}")
    assert resp.status_code == 200
    assert resp.json()["ref_id"] == ref_id
    assert resp.json()["attachment"] is None


@pytest.mark.asyncio
async def test_get_contract_not_found(client):
    resp = await client.get(f"{BASE}/CON-9999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_contract_draft(client, test_account):
    create = await client.post(BASE, json={
        "value": 2000.0,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "account_id": test_account.id,
    })
    ref_id = create.json()["ref_id"]

    resp = await client.patch(f"{BASE}/{ref_id}", json={"value": 3000.0})
    assert resp.status_code == 200
    assert float(resp.json()["value"]) == 3000.0


@pytest.mark.asyncio
async def test_full_transition_chain(client, admin_client, test_account):
    """Draft → SFR → Active → Expired."""
    create = await client.post(BASE, json={
        "value": 1000.0,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "account_id": test_account.id,
    })
    ref_id = create.json()["ref_id"]

    r1 = await client.post(f"{BASE}/{ref_id}/transition",
                           json={"status": "Sent for Review"})
    assert r1.status_code == 200

    r2 = await client.post(f"{BASE}/{ref_id}/transition",
                           json={"status": "Active"})
    assert r2.status_code == 200

    r3 = await admin_client.post(f"{BASE}/{ref_id}/transition",
                                 json={"status": "Expired", "note": "Admin forced"})
    assert r3.status_code == 200
    assert r3.json()["new_status"] == "Expired"


@pytest.mark.asyncio
async def test_attachment_upload_and_delete(client, test_account):
    create = await client.post(BASE, json={
        "value": 1000.0,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "account_id": test_account.id,
    })
    ref_id = create.json()["ref_id"]

    pdf_bytes = b"%PDF-1.4 fake content"
    files = {"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    upload = await client.post(f"{BASE}/{ref_id}/attachment", files=files)
    assert upload.status_code == 201
    assert upload.json()["filename"] == "test.pdf"

    detail = await client.get(f"{BASE}/{ref_id}")
    assert detail.json()["attachment"] is not None

    delete = await client.delete(f"{BASE}/{ref_id}/attachment")
    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_attachment_size_limit(client, test_account):
    create = await client.post(BASE, json={
        "value": 1000.0,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "account_id": test_account.id,
    })
    ref_id = create.json()["ref_id"]

    big = b"x" * (1_048_576 + 1)
    files = {"file": ("big.pdf", io.BytesIO(big), "application/pdf")}
    resp = await client.post(f"{BASE}/{ref_id}/attachment", files=files)
    assert resp.status_code == 413


@pytest.mark.asyncio
async def test_activity_log_retrieval(client, test_account):
    create = await client.post(BASE, json={
        "value": 1000.0,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "account_id": test_account.id,
    })
    ref_id = create.json()["ref_id"]
    await client.post(f"{BASE}/{ref_id}/transition", json={"status": "Sent for Review"})

    resp = await client.get(f"{BASE}/{ref_id}/activity")
    assert resp.status_code == 200
    logs = resp.json()["logs"]
    assert len(logs) >= 2
    action_types = [l["action_type"] for l in logs]
    assert "status_transition" in action_types


@pytest.mark.asyncio
async def test_list_contracts_filter_by_status(client, test_account):
    for i in range(3):
        await client.post(BASE, json={
            "value": 1000.0 * (i + 1),
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "account_id": test_account.id,
        })

    resp = await client.get(f"{BASE}?status=Draft")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 3
    for item in resp.json()["items"]:
        assert item["status"] == "Draft"
