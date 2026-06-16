from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user
from app.schemas.contact import (
    AccountDetailResponse,
    AccountResponse,
    CreateAccountRequest,
    PaginatedAccounts,
    TimelineItem,
    UpdateAccountRequest,
)
from app.services.account_service import AccountService

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=PaginatedAccounts)
async def list_accounts(
    q: str | None = None,
    industry: str | None = None,
    owner_id: int | None = None,
    include_archived: bool = False,
    cursor: str | None = None,
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PaginatedAccounts:
    svc = AccountService(session)
    return await svc.list(q=q, industry=industry, owner_id=owner_id,
                           include_archived=include_archived, cursor=cursor, limit=limit)


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: CreateAccountRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AccountResponse:
    if current_user.role == "Support Agent":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Access denied.")
    svc = AccountService(session)
    account = await svc.create(payload.model_dump(), current_user)
    return AccountResponse.model_validate(account)


@router.get("/{account_id}", response_model=AccountDetailResponse)
async def get_account(
    account_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AccountDetailResponse:
    svc = AccountService(session)
    return await svc.get(account_id)


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    payload: UpdateAccountRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AccountResponse:
    svc = AccountService(session)
    account = await svc.update(account_id, payload.model_dump(exclude_none=True), current_user)
    return AccountResponse.model_validate(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_account(
    account_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if current_user.role != "Admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin only.")
    svc = AccountService(session)
    await svc.archive(account_id, current_user)


@router.get("/{account_id}/timeline", response_model=list[TimelineItem])
async def get_account_timeline(
    account_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[TimelineItem]:
    svc = AccountService(session)
    return await svc.get_timeline(account_id)
