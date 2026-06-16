"""Integration tests for deal activity log endpoint."""

import pytest


async def _create_deal(client, test_user, test_account, **kwargs):
    payload = {
        "title": "Activity Test Deal",
        "value": "1000.00",
        "stage": "Lead In",
        "expected_close_date": "2026-12-31",
        "owner_id": test_user.id,
        "account_id": test_account.id,
        **kwargs,
    }
    resp = await client.post("/api/v1/deals", json=payload)
    assert resp.status_code == 201
    return resp.json()["ref_id"]


@pytest.mark.asyncio
async def test_deal_created_entry_on_create(client, test_user, test_account):
    ref_id = await _create_deal(client, test_user, test_account)

    resp = await client.get(f"/api/v1/deals/{ref_id}/activity")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    actions = [e["action_type"] for e in data["items"]]
    assert "deal_created" in actions


@pytest.mark.asyncio
async def test_field_updated_entry_on_patch(client, test_user, test_account):
    ref_id = await _create_deal(client, test_user, test_account)
    await client.patch(f"/api/v1/deals/{ref_id}", json={"value": "9999.00"})

    resp = await client.get(f"/api/v1/deals/{ref_id}/activity")
    assert resp.status_code == 200
    actions = [e["action_type"] for e in resp.json()["items"]]
    assert "field_updated" in actions


@pytest.mark.asyncio
async def test_activity_log_ascending_order(client, test_user, test_account):
    ref_id = await _create_deal(client, test_user, test_account)
    await client.patch(f"/api/v1/deals/{ref_id}", json={"title": "Updated"})
    await client.post(f"/api/v1/deals/{ref_id}/stage", json={"stage": "Qualified"})

    resp = await client.get(f"/api/v1/deals/{ref_id}/activity")
    items = resp.json()["items"]
    timestamps = [e["created_at"] for e in items]
    assert timestamps == sorted(timestamps)
