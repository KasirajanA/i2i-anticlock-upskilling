"""Integration tests for deal comments endpoints."""

import pytest


async def _create_deal(client, test_user, test_account):
    resp = await client.post("/api/v1/deals", json={
        "title": "Deal with Comments",
        "value": "1000.00",
        "stage": "Lead In",
        "expected_close_date": "2026-12-31",
        "owner_id": test_user.id,
        "account_id": test_account.id,
    })
    assert resp.status_code == 201
    return resp.json()["ref_id"]


@pytest.mark.asyncio
async def test_add_comment_returns_201(client, test_user, test_account):
    ref_id = await _create_deal(client, test_user, test_account)
    resp = await client.post(f"/api/v1/deals/{ref_id}/comments", json={"body": "Great progress!"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["body"] == "Great progress!"
    assert data["author"]["id"] == test_user.id


@pytest.mark.asyncio
async def test_list_comments_returns_200(client, test_user, test_account):
    ref_id = await _create_deal(client, test_user, test_account)
    await client.post(f"/api/v1/deals/{ref_id}/comments", json={"body": "First comment"})
    await client.post(f"/api/v1/deals/{ref_id}/comments", json={"body": "Second comment"})

    resp = await client.get(f"/api/v1/deals/{ref_id}/comments")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_empty_body_returns_400(client, test_user, test_account):
    ref_id = await _create_deal(client, test_user, test_account)
    resp = await client.post(f"/api/v1/deals/{ref_id}/comments", json={"body": "   "})
    assert resp.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_comment_on_nonexistent_deal_returns_404(client):
    resp = await client.post("/api/v1/deals/DEAL-XXXX/comments", json={"body": "Test"})
    assert resp.status_code == 404
