"""Contract business logic — all state-mutation rules live here, not in route handlers."""

import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import CurrentUser, assert_contract_ownership
from app.models.contracts import (
    ActivityLog,
    Contract,
    ContractAttachment,
    ContractStatus,
    RenewalLink,
)
from app.repositories.contract_repository import ContractRepository
from app.schemas.contracts import ContractCreate, ContractUpdate

# ---------------------------------------------------------------------------
# Status state-machine — data-driven to keep cyclomatic complexity ≤ 5
# (from_status, role) → set of permitted target statuses
# ---------------------------------------------------------------------------
_FORWARD: dict[tuple[ContractStatus, str], set[ContractStatus]] = {
    (ContractStatus.DRAFT, "Sales Rep"): {ContractStatus.SENT_FOR_REVIEW},
    (ContractStatus.DRAFT, "Manager"): {ContractStatus.SENT_FOR_REVIEW},
    (ContractStatus.DRAFT, "Admin"): {ContractStatus.SENT_FOR_REVIEW},
    (ContractStatus.SENT_FOR_REVIEW, "Sales Rep"): {ContractStatus.ACTIVE},
    (ContractStatus.SENT_FOR_REVIEW, "Manager"): {ContractStatus.ACTIVE},
    (ContractStatus.SENT_FOR_REVIEW, "Admin"): {ContractStatus.ACTIVE},
    (ContractStatus.ACTIVE, "Sales Rep"): {ContractStatus.TERMINATED},
    (ContractStatus.ACTIVE, "Manager"): {ContractStatus.TERMINATED},
    (ContractStatus.ACTIVE, "Admin"): {ContractStatus.TERMINATED, ContractStatus.EXPIRED},
}

_ALL_STATUSES: set[ContractStatus] = set(ContractStatus)

VALID_TRANSITIONS: dict[tuple[ContractStatus, str], set[ContractStatus]] = {
    **_FORWARD,
    # Admin backward revert to any status (requires note)
    (ContractStatus.SENT_FOR_REVIEW, "Admin"): _ALL_STATUSES - {ContractStatus.SENT_FOR_REVIEW},
    (ContractStatus.ACTIVE, "Admin"): _ALL_STATUSES - {ContractStatus.ACTIVE},
    (ContractStatus.EXPIRED, "Admin"): _ALL_STATUSES - {ContractStatus.EXPIRED},
    (ContractStatus.TERMINATED, "Admin"): _ALL_STATUSES - {ContractStatus.TERMINATED},
}

_STATUS_ORDER = [
    ContractStatus.DRAFT,
    ContractStatus.SENT_FOR_REVIEW,
    ContractStatus.ACTIVE,
    ContractStatus.EXPIRED,
    ContractStatus.TERMINATED,
]


def _is_backward(from_status: ContractStatus, to_status: ContractStatus) -> bool:
    """Determine if a status transition moves backward in the workflow."""
    try:
        return _STATUS_ORDER.index(to_status) < _STATUS_ORDER.index(from_status)
    except ValueError:
        return False


class ContractService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = ContractRepository(db)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create(
        self, payload: ContractCreate, current_user: CurrentUser
    ) -> Contract:
        from sqlalchemy import select  # noqa: PLC0415
        from app.models.contact import Account  # noqa: PLC0415
        from app.models.deal import Deal  # noqa: PLC0415

        # FK existence checks
        account = await self._db.get(Account, payload.account_id)
        if account is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found")

        if payload.deal_id is not None:
            deal = await self._db.get(Deal, payload.deal_id)
            if deal is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Deal not found")

        owner_id = payload.owner_id
        if owner_id is None:
            owner_id = current_user.id
        elif current_user.role not in ("Admin", "Manager"):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Only Admin and Manager may assign a different owner",
            )

        seq = await self._repo.get_next_seq()
        ref_id = f"CON-{seq:04d}"

        contract = Contract(
            ref_id=ref_id,
            value=payload.value,
            start_date=payload.start_date,
            end_date=payload.end_date,
            description=payload.description,
            account_id=payload.account_id,
            deal_id=payload.deal_id,
            owner_id=owner_id,
            status=ContractStatus.DRAFT,
        )
        contract = await self._repo.create(contract)

        self._db.add(
            ActivityLog(
                contract_id=contract.id,
                action_type="status_transition",
                actor_id=current_user.id,
                note=f"Contract created with status {ContractStatus.DRAFT.value}",
            )
        )
        await self._db.flush()
        return contract

    # ------------------------------------------------------------------
    # Update editable fields
    # ------------------------------------------------------------------

    async def update(
        self, contract: Contract, payload: ContractUpdate, current_user: CurrentUser
    ) -> Contract:
        if contract.status not in (ContractStatus.DRAFT, ContractStatus.SENT_FOR_REVIEW):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Contracts in '{contract.status.value}' status cannot be edited.",
            )
        assert_contract_ownership(contract.owner_id, current_user)

        updates = payload.model_dump(exclude_unset=True)

        # Cross-field date validation when only one date is in the payload
        new_start = updates.get("start_date", contract.start_date)
        new_end = updates.get("end_date", contract.end_date)
        if new_end < new_start:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "end_date must be on or after start_date"
            )

        contract = await self._repo.update(contract, **updates)
        self._db.add(
            ActivityLog(
                contract_id=contract.id,
                action_type="edit",
                actor_id=current_user.id,
                note=f"Fields updated: {', '.join(updates.keys())}",
            )
        )
        await self._db.flush()
        return contract

    # ------------------------------------------------------------------
    # Lifecycle transitions
    # ------------------------------------------------------------------

    async def transition(
        self,
        contract: Contract,
        to_status: ContractStatus,
        note: str | None,
        current_user: CurrentUser,
    ) -> tuple[ContractStatus, datetime]:
        from_status = contract.status

        # Backward-transition guard runs first so the API returns 403 (not 400)
        # when a non-Admin user attempts a revert — matches the API contract spec.
        if _is_backward(from_status, to_status):
            if current_user.role != "Admin":
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN,
                    "Only Admins may revert a contract to a prior status.",
                )
            if not note:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    "A note is required for backward status transitions.",
                )

        allowed = VALID_TRANSITIONS.get((from_status, current_user.role), set())
        if to_status not in allowed:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Transition from '{from_status.value}' to '{to_status.value}' is not allowed for role '{current_user.role}'.",
            )

        assert_contract_ownership(contract.owner_id, current_user)

        await self._repo.update(contract, status=to_status)
        log = ActivityLog(
            contract_id=contract.id,
            action_type="status_transition",
            actor_id=current_user.id,
            note=note or f"{from_status.value} → {to_status.value}",
        )
        self._db.add(log)
        await self._db.flush()
        await self._db.refresh(log)
        return from_status, log.created_at

    # ------------------------------------------------------------------
    # Attachment management
    # ------------------------------------------------------------------

    async def replace_attachment(
        self,
        contract: Contract,
        file: UploadFile,
        current_user: CurrentUser,
    ) -> ContractAttachment:
        assert_contract_ownership(contract.owner_id, current_user)

        content = await file.read()
        size = len(content)

        if size > settings.max_attachment_bytes:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds 1 MB limit")

        mime = file.content_type or ""
        if mime not in settings.allowed_mime_types:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"MIME type '{mime}' is not allowed. Accepted: PDF, DOCX, JPEG, PNG.",
            )

        # Atomic replace: delete old → write new → update DB — all in one flush
        if contract.attachment:
            old_path = Path(contract.attachment.storage_path)
            if old_path.exists():
                old_path.unlink()
            await self._db.delete(contract.attachment)
            await self._db.flush()

        dest_dir = settings.attachment_dir / str(contract.id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / (file.filename or "attachment")
        dest_path.write_bytes(content)

        attachment = ContractAttachment(
            contract_id=contract.id,
            filename=file.filename or "attachment",
            mime_type=mime,
            size_bytes=size,
            storage_path=str(dest_path),
        )
        self._db.add(attachment)
        self._db.add(
            ActivityLog(
                contract_id=contract.id,
                action_type="attachment_added",
                actor_id=current_user.id,
                note=file.filename,
            )
        )
        await self._db.flush()
        await self._db.refresh(attachment)
        return attachment

    async def delete_attachment(
        self, contract: Contract, current_user: CurrentUser
    ) -> None:
        assert_contract_ownership(contract.owner_id, current_user)

        if contract.attachment is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No attachment on this contract")

        path = Path(contract.attachment.storage_path)
        if path.exists():
            path.unlink()

        await self._db.delete(contract.attachment)
        self._db.add(
            ActivityLog(
                contract_id=contract.id,
                action_type="attachment_removed",
                actor_id=current_user.id,
            )
        )
        await self._db.flush()

    # ------------------------------------------------------------------
    # Renewal
    # ------------------------------------------------------------------

    async def renew(
        self, contract: Contract, current_user: CurrentUser
    ) -> tuple[Contract, "RenewalLink"]:
        assert_contract_ownership(contract.owner_id, current_user)

        if contract.status not in (ContractStatus.ACTIVE, ContractStatus.EXPIRED):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Only Active or Expired contracts can be renewed.",
            )

        if contract.renewal_as_original is not None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "A renewal already exists for this contract."
            )

        term = contract.end_date - contract.start_date
        new_start = contract.end_date + timedelta(days=1)
        new_end = new_start + term

        seq = await self._repo.get_next_seq()
        successor = Contract(
            ref_id=f"CON-{seq:04d}",
            value=contract.value,
            start_date=new_start,
            end_date=new_end,
            description=contract.description,
            account_id=contract.account_id,
            deal_id=contract.deal_id,
            owner_id=contract.owner_id,
            status=ContractStatus.DRAFT,
        )
        successor = await self._repo.create(successor)

        link = RenewalLink(
            original_contract_id=contract.id,
            successor_contract_id=successor.id,
        )
        self._db.add(link)
        self._db.add(
            ActivityLog(
                contract_id=contract.id,
                action_type="renewed",
                actor_id=current_user.id,
                note=f"Renewed as {successor.ref_id}",
            )
        )
        await self._db.flush()
        await self._db.refresh(link)
        return successor, link
