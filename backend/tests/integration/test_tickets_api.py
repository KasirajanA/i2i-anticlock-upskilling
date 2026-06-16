"""Integration tests for /api/v1/support/tickets endpoints."""

import pytest


def _ticket_payload(contact_id: int) -> dict:
    return {
        "subject": "Login page broken",
        "description": "Users cannot log in.",
        "priority": "high",
        "contact_id": contact_id,
    }


@pytest.mark.asyncio
async def test_create_ticket_returns_201(
    support_client, test_contact, support_agent_user
):
    resp = await support_client.post(
        "/api/v1/support/tickets", json=_ticket_payload(test_contact.id)
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["ref"].startswith("I2I-CRM-")
    assert data["status"] == "open"
    assert data["priority"] == "high"
    assert data["sla"] is not None
    assert "first_response_due" in data["sla"]


@pytest.mark.asyncio
async def test_create_ticket_invalid_contact_returns_422(
    support_client,
):
    resp = await support_client.post(
        "/api/v1/support/tickets",
        json={"subject": "Test", "priority": "low", "contact_id": 99999},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_ticket_returns_200(support_client, test_contact):
    create = await support_client.post(
        "/api/v1/support/tickets", json=_ticket_payload(test_contact.id)
    )
    ticket_id = create.json()["id"]

    resp = await support_client.get(f"/api/v1/support/tickets/{ticket_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == ticket_id


@pytest.mark.asyncio
async def test_get_ticket_not_found_returns_404(support_client):
    resp = await support_client.get("/api/v1/support/tickets/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_tickets_returns_200(support_client, test_contact):
    for _ in range(3):
        await support_client.post(
            "/api/v1/support/tickets", json=_ticket_payload(test_contact.id)
        )
    resp = await support_client.get("/api/v1/support/tickets")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3


@pytest.mark.asyncio
async def test_list_tickets_queue_mine(
    support_client, admin_client, test_contact, support_agent_user
):
    """My queue shows only tickets assigned to current user."""
    # Create a ticket assigned to the agent
    create = await support_client.post(
        "/api/v1/support/tickets",
        json={**_ticket_payload(test_contact.id), "assignee_id": support_agent_user.id},
    )
    assert create.status_code == 201

    resp = await support_client.get("/api/v1/support/tickets?queue=mine")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(item["assignee_id"] == support_agent_user.id for item in items)


@pytest.mark.asyncio
async def test_list_tickets_queue_unassigned(support_client, test_contact):
    """Unassigned queue shows tickets with no assignee."""
    await support_client.post(
        "/api/v1/support/tickets", json=_ticket_payload(test_contact.id)
    )
    resp = await support_client.get("/api/v1/support/tickets?queue=unassigned")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(item["assignee_id"] is None for item in items)


@pytest.mark.asyncio
async def test_patch_ticket_status_transition(support_client, test_contact):
    create = await support_client.post(
        "/api/v1/support/tickets", json=_ticket_payload(test_contact.id)
    )
    ticket_id = create.json()["id"]

    resp = await support_client.patch(
        f"/api/v1/support/tickets/{ticket_id}", json={"status": "in_progress"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_patch_ticket_invalid_transition_returns_422(
    support_client, test_contact
):
    create = await support_client.post(
        "/api/v1/support/tickets", json=_ticket_payload(test_contact.id)
    )
    ticket_id = create.json()["id"]

    resp = await support_client.patch(
        f"/api/v1/support/tickets/{ticket_id}", json={"status": "closed"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_assign_self_assign_allowed(
    support_client, test_contact, support_agent_user
):
    create = await support_client.post(
        "/api/v1/support/tickets", json=_ticket_payload(test_contact.id)
    )
    ticket_id = create.json()["id"]

    resp = await support_client.post(
        f"/api/v1/support/tickets/{ticket_id}/assign",
        json={"assignee_id": support_agent_user.id},
    )
    assert resp.status_code == 200
    assert resp.json()["assignee_id"] == support_agent_user.id


@pytest.mark.asyncio
async def test_sales_rep_cannot_create_ticket(client, test_contact):
    """Sales Rep role should receive 403."""
    resp = await client.post(
        "/api/v1/support/tickets", json=_ticket_payload(test_contact.id)
    )
    assert resp.status_code == 403
