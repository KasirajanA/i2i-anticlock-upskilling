"""All /api/v1/contracts route handlers."""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user, require_roles
from app.models.base import User
from app.models.contracts import ActivityLog, Contract
from app.repositories.contract_repository import ContractRepository
from app.schemas.contracts import (
    ActivityLogEntry,
    ActivityLogResponse,
    AttachmentResponse,
    ContractCreate,
    ContractFilterParams,
    ContractListResponse,
    ContractResponse,
    ContractUpdate,
    RenewResponse,
    TransitionRequest,
    TransitionResponse,
)
from app.services.contract_service import ContractService

router = APIRouter(prefix="/contracts", tags=["contracts"])


def _svc(db: AsyncSession = Depends(get_session)) -> ContractService:
    return ContractService(db)


async def _get_contract_or_404(ref_id: str, db: AsyncSession) -> Contract:
    repo = ContractRepository(db)
    contract = await repo.get_by_ref_id(ref_id)
    if contract is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Contract '{ref_id}' not found")
    return contract


# ---------------------------------------------------------------------------
# List & Create
# ---------------------------------------------------------------------------

@router.get("", response_model=ContractListResponse)
async def list_contracts(
    filters: ContractFilterParams = Depends(),
    db: AsyncSession = Depends(get_session),
    _: CurrentUser = Depends(get_current_user),
) -> ContractListResponse:
    repo = ContractRepository(db)
    total, items = await repo.list_paginated(
        status=filters.status,
        owner_id=filters.owner_id,
        account_id=filters.account_id,
        end_date_from=filters.end_date_from,
        end_date_to=filters.end_date_to,
        is_renewal_due=filters.is_renewal_due,
        page=filters.page,
        limit=filters.limit,
    )
    return ContractListResponse(
        total=total, page=filters.page, limit=filters.limit, items=items
    )


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    payload: ContractCreate,
    svc: ContractService = Depends(_svc),
    current_user: CurrentUser = Depends(require_roles("Sales Rep", "Admin", "Manager")),
    db: AsyncSession = Depends(get_session),
) -> ContractResponse:
    contract = await svc.create(payload, current_user)
    await db.commit()
    repo = ContractRepository(db)
    contract = await repo.get_by_ref_id(contract.ref_id)
    return ContractResponse.model_validate(contract)


# ---------------------------------------------------------------------------
# Single contract CRUD
# ---------------------------------------------------------------------------

@router.get("/{ref_id}", response_model=ContractResponse)
async def get_contract(
    ref_id: str,
    db: AsyncSession = Depends(get_session),
    _: CurrentUser = Depends(get_current_user),
) -> ContractResponse:
    contract = await _get_contract_or_404(ref_id, db)
    return ContractResponse.model_validate(contract)


@router.patch("/{ref_id}", response_model=ContractResponse)
async def update_contract(
    ref_id: str,
    payload: ContractUpdate,
    svc: ContractService = Depends(_svc),
    current_user: CurrentUser = Depends(require_roles("Sales Rep", "Admin", "Manager")),
    db: AsyncSession = Depends(get_session),
) -> ContractResponse:
    contract = await _get_contract_or_404(ref_id, db)
    contract = await svc.update(contract, payload, current_user)
    await db.commit()
    repo = ContractRepository(db)
    contract = await repo.get_by_ref_id(contract.ref_id)
    return ContractResponse.model_validate(contract)


# ---------------------------------------------------------------------------
# Lifecycle transition
# ---------------------------------------------------------------------------

@router.post("/{ref_id}/transition", response_model=TransitionResponse)
async def transition_contract(
    ref_id: str,
    payload: TransitionRequest,
    svc: ContractService = Depends(_svc),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> TransitionResponse:
    contract = await _get_contract_or_404(ref_id, db)
    previous, logged_at = await svc.transition(
        contract, payload.status, payload.note, current_user
    )
    await db.commit()
    return TransitionResponse(
        ref_id=ref_id,
        previous_status=previous,
        new_status=payload.status,
        logged_at=logged_at,
    )


# ---------------------------------------------------------------------------
# Activity log
# ---------------------------------------------------------------------------

@router.get("/{ref_id}/activity", response_model=ActivityLogResponse)
async def get_activity_log(
    ref_id: str,
    db: AsyncSession = Depends(get_session),
    _: CurrentUser = Depends(get_current_user),
) -> ActivityLogResponse:
    contract = await _get_contract_or_404(ref_id, db)

    result = await db.execute(
        select(ActivityLog, User.name.label("actor_name"))
        .outerjoin(User, ActivityLog.actor_id == User.id)
        .where(ActivityLog.contract_id == contract.id)
        .order_by(ActivityLog.created_at.desc())
    )
    rows = result.all()

    logs = [
        ActivityLogEntry(
            id=row.ActivityLog.id,
            action_type=row.ActivityLog.action_type,
            actor_id=row.ActivityLog.actor_id,
            actor_name=row.actor_name or "System",
            note=row.ActivityLog.note,
            created_at=row.ActivityLog.created_at,
        )
        for row in rows
    ]
    return ActivityLogResponse(ref_id=ref_id, logs=logs)


# ---------------------------------------------------------------------------
# Renewal
# ---------------------------------------------------------------------------

@router.post(
    "/{ref_id}/renew",
    response_model=RenewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def renew_contract(
    ref_id: str,
    svc: ContractService = Depends(_svc),
    current_user: CurrentUser = Depends(require_roles("Sales Rep", "Admin", "Manager")),
    db: AsyncSession = Depends(get_session),
) -> RenewResponse:
    contract = await _get_contract_or_404(ref_id, db)
    successor, _ = await svc.renew(contract, current_user)
    await db.commit()
    repo = ContractRepository(db)
    successor = await repo.get_by_ref_id(successor.ref_id)
    return RenewResponse(
        original_ref_id=ref_id,
        successor=ContractResponse.model_validate(successor),
    )


# ---------------------------------------------------------------------------
# Attachment
# ---------------------------------------------------------------------------

@router.post(
    "/{ref_id}/attachment",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    ref_id: str,
    file: UploadFile = File(...),
    svc: ContractService = Depends(_svc),
    current_user: CurrentUser = Depends(require_roles("Sales Rep", "Admin", "Manager")),
    db: AsyncSession = Depends(get_session),
) -> AttachmentResponse:
    contract = await _get_contract_or_404(ref_id, db)
    attachment = await svc.replace_attachment(contract, file, current_user)
    await db.commit()
    await db.refresh(attachment)
    return AttachmentResponse.model_validate(attachment)


@router.delete(
    "/{ref_id}/attachment",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_attachment(
    ref_id: str,
    svc: ContractService = Depends(_svc),
    current_user: CurrentUser = Depends(require_roles("Sales Rep", "Admin", "Manager")),
    db: AsyncSession = Depends(get_session),
) -> None:
    contract = await _get_contract_or_404(ref_id, db)
    await svc.delete_attachment(contract, current_user)
    await db.commit()


# ---------------------------------------------------------------------------
# Internal job triggers (Admin-only; for testing and on-demand execution)
# ---------------------------------------------------------------------------

internal_router = APIRouter(prefix="/internal/jobs", tags=["internal"])


@internal_router.post("/expire-contracts")
async def trigger_expire_contracts(
    _: CurrentUser = Depends(require_roles("Admin")),
    db: AsyncSession = Depends(get_session),
) -> dict:
    from app.scheduler.jobs import _run_expire_with_session  # noqa: PLC0415

    count = await _run_expire_with_session(db)
    await db.commit()
    return {"expired": count}


@internal_router.post("/flag-renewals")
async def trigger_flag_renewals(
    _: CurrentUser = Depends(require_roles("Admin")),
    db: AsyncSession = Depends(get_session),
) -> dict:
    from app.scheduler.jobs import _run_flag_renewals_with_session  # noqa: PLC0415

    count = await _run_flag_renewals_with_session(db)
    await db.commit()
    return {"flagged": count}
