"""Integration tests for GET /api/v1/analytics/reports/support."""

import pytest


@pytest.mark.asyncio
async def test_support_report_returns_200(admin_client):
    resp = await admin_client.get("/api/v1/analytics/reports/support")
    assert resp.status_code == 200
    body = resp.json()
    assert "status_breakdown" in body
    assert "sla_breach_rate" in body
    assert "per_agent" in body


@pytest.mark.asyncio
async def test_support_agent_owner_id_override_returns_403(support_client, admin_user):
    resp = await support_client.get(f"/api/v1/analytics/reports/support?assignee_id={admin_user.id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_cached_until_is_within_60_seconds(admin_client):
    from datetime import datetime, timedelta  # noqa: PLC0415
    resp = await admin_client.get("/api/v1/analytics/reports/support")
    assert resp.status_code == 200
    cached_until = resp.json().get("cached_until")
    assert cached_until is not None
    dt = datetime.fromisoformat(cached_until)
    # Should be ≤ 61 seconds from now
    assert dt <= datetime.utcnow() + timedelta(seconds=61)


@pytest.mark.asyncio
async def test_support_export_returns_csv(support_client):
    resp = await support_client.get("/api/v1/analytics/reports/support/export")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
