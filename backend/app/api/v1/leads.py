from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user
from app.schemas.contact import (
    ConversionResult,
    ConvertLeadRequest,
    CreateLeadRequest,
    LeadResponse,
    PaginatedLeads,
    UpdateLeadRequest,
)
from app.services.lead_service import LeadService

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=PaginatedLeads)
async def list_leads(
    status: str | None = None,
    q: str | None = None,
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PaginatedLeads:
    svc = LeadService(session)
    return await svc.list(current_user, status_filter=status, q=q, limit=limit)


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: CreateLeadRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LeadResponse:
    svc = LeadService(session)
    lead = await svc.create(payload.model_dump(), current_user)
    return LeadResponse.model_validate(lead)


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    payload: UpdateLeadRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> LeadResponse:
    svc = LeadService(session)
    data = payload.model_dump(exclude_none=True)
    if "status" in data:
        lead = await svc.update_status(lead_id, data["status"], current_user)
    else:
        lead = await svc._repo.update(lead_id, data)
        if lead is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Lead not found.")
    return LeadResponse.model_validate(lead)


@router.post("/{lead_id}/convert", response_model=ConversionResult, status_code=status.HTTP_201_CREATED)
async def convert_lead(
    lead_id: int,
    payload: ConvertLeadRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ConversionResult:
    if current_user.role not in ("Admin", "Sales Rep"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Access denied.")
    svc = LeadService(session)
    return await svc.convert(lead_id, payload, current_user)
