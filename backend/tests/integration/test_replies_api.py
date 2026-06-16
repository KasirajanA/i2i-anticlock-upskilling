"""Integration tests for support ticket replies and re-open logic."""

import pytest


async def _create_ticket(client, contact_id: int) -> int:
    resp = await client.post(
        "/api/v1/support/tickets",
        json={"subject": "Test", "priority": "low", "contact_id": contact_id},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_add_reply_returns_201(support_client, test_contact):
    ticket_id = await _create_ticket(support_client, test_contact.id)
    resp = await support_client.post(
        f"/api/v1/support/tickets/{ticket_id}/replies",
        json={"body": "We are investigating.", "is_internal": False},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["body"] == "We are investigating."
    assert data["is_internal"] is False


@pytest.mark.asyncio
async def test_list_replies_returns_200(support_client, test_contact):
    ticket_id = await _create_ticket(support_client, test_contact.id)
    await support_client.post(
        f"/api/v1/support/tickets/{ticket_id}/replies",
        json={"body": "Reply 1", "is_internal": False},
    )
    resp = await support_client.get(
        f"/api/v1/support/tickets/{ticket_id}/replies"
    )
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1


@pytest.mark.asyncio
async def test_internal_note_hidden_from_sales_rep(
    support_client, client, test_contact
):
    """Sales Rep (non-agent) should not see internal notes."""
    ticket_id = await _create_ticket(support_client, test_contact.id)
    await support_client.post(
        f"/api/v1/support/tickets/{ticket_id}/replies",
        json={"body": "Secret note", "is_internal": True},
    )

    # Sales Rep client should get 0 items (internal note filtered)
    resp = await client.get(f"/api/v1/support/tickets/{ticket_id}/replies")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(not item["is_internal"] for item in items)


@pytest.mark.asyncio
async def test_first_response_at_set_on_first_non_internal_reply(
    support_client, test_contact
):
    ticket_id = await _create_ticket(support_client, test_contact.id)

    # Check SLA before reply
    sla_before = (
        await support_client.get(f"/api/v1/support/tickets/{ticket_id}/sla")
    ).json()["items"][0]
    assert sla_before["first_response_at"] is None

    # Add a public reply
    await support_client.post(
        f"/api/v1/support/tickets/{ticket_id}/replies",
        json={"body": "First reply", "is_internal": False},
    )

    sla_after = (
        await support_client.get(f"/api/v1/support/tickets/{ticket_id}/sla")
    ).json()["items"][0]
    assert sla_after["first_response_at"] is not None


@pytest.mark.asyncio
async def test_reply_on_resolved_ticket_reopens(support_client, test_contact):
    ticket_id = await _create_ticket(support_client, test_contact.id)

    # Advance to resolved
    await support_client.patch(
        f"/api/v1/support/tickets/{ticket_id}", json={"status": "in_progress"}
    )
    await support_client.patch(
        f"/api/v1/support/tickets/{ticket_id}", json={"status": "resolved"}
    )

    # Verify resolved
    ticket = (
        await support_client.get(f"/api/v1/support/tickets/{ticket_id}")
    ).json()
    assert ticket["status"] == "resolved"

    # Customer reply → should reopen
    await support_client.post(
        f"/api/v1/support/tickets/{ticket_id}/replies",
        json={"body": "Issue still present", "is_internal": False},
    )

    updated = (
        await support_client.get(f"/api/v1/support/tickets/{ticket_id}")
    ).json()
    assert updated["status"] == "open"

    # New SLA cycle should be active
    sla_resp = (
        await support_client.get(f"/api/v1/support/tickets/{ticket_id}/sla")
    ).json()["items"]
    assert len(sla_resp) == 2
    active = [s for s in sla_resp if s["is_active"]]
    assert len(active) == 1
    assert active[0]["cycle"] == 2
