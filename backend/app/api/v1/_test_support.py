"""Test-only endpoints for the Customer Support module.

Enabled ONLY when ENVIRONMENT=test. These endpoints are never registered
in production builds — the router is conditionally imported in main.py.
"""

import os

from fastapi import APIRouter, HTTPException, Query, status

from app.services import sla_engine as _sla_module

router = APIRouter(prefix="/api/v1/_test", tags=["test-only"])


def _guard() -> None:
    if os.getenv("ENVIRONMENT", "production").lower() != "test":
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Test endpoints are not available in production.",
        )


@router.post("/sla/advance-clock")
async def advance_clock(minutes: int = Query(..., gt=0)) -> dict:
    _guard()
    _sla_module._clock_offset_seconds += minutes * 60
    return {"offset_seconds": _sla_module._clock_offset_seconds}


@router.post("/jobs/run-sla-check")
async def run_sla_check() -> dict:
    _guard()
    from app.core.database import get_session  # noqa: PLC0415
    from app.scheduler.jobs import _run_sla_breach_with_session  # noqa: PLC0415

    # Create a fresh DB session for the job
    async for session in get_session():
        breached = await _run_sla_breach_with_session(session)
        await session.commit()
        return {"breached_ticket_ids": breached}
    return {"breached_ticket_ids": []}
