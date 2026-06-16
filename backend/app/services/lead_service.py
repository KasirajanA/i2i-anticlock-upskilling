from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.repositories.sqlite_lead_repository import SqliteLeadRepository
from app.schemas.contact import (
    ConversionResult,
    ConvertLeadRequest,
    LeadResponse,
    PaginatedLeads,
)
from app.services.contact_activity_logger import ContactActivityLogger

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "new": {"contacted"},
    "contacted": {"qualified", "disqualified"},
    "qualified": {"converted", "disqualified"},
    "converted": set(),
    "disqualified": set(),
}


class LeadService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session
        self._repo = SqliteLeadRepository(session)
        self._logger = ContactActivityLogger()

    async def create(self, data: dict, actor: CurrentUser):
        if actor.role not in ("Admin", "Sales Rep"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only Admins and Sales Reps can create leads.")
        if not data.get("owner_id"):
            data["owner_id"] = actor.id
        lead = await self._repo.create(data)
        await self._logger.log(self._db, "created", "lead", lead.id, actor.id)
        await self._db.commit()
        return lead

    async def get(self, id: int) -> LeadResponse:
        lead = await self._repo.get_by_id(id)
        if lead is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Lead not found.")
        return LeadResponse.model_validate(lead)

    async def list(
        self,
        actor: CurrentUser,
        status_filter: str | None = None,
        q: str | None = None,
        limit: int = 50,
    ) -> PaginatedLeads:
        owner_id = None
        if actor.role == "Sales Rep":
            owner_id = actor.id
        elif actor.role == "Support Agent":
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Access denied.")
        return await self._repo.list(status=status_filter, owner_id=owner_id, q=q, limit=limit)

    async def update_status(self, id: int, new_status: str, actor: CurrentUser):
        lead = await self._repo.get_by_id(id)
        if lead is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Lead not found.")
        if lead.status in ("converted", "disqualified"):
            raise HTTPException(status.HTTP_409_CONFLICT, detail=f"Lead is already {lead.status}.")
        allowed = ALLOWED_TRANSITIONS.get(lead.status, set())
        if new_status not in allowed and actor.role != "Admin":
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot transition from {lead.status} to {new_status}.",
            )
        updates: dict = {"status": new_status}
        if new_status == "disqualified" and not lead.disqualify_reason:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="disqualify_reason required when status=disqualified.",
            )
        updated = await self._repo.update(id, updates)
        await self._logger.log(self._db, f"status_changed:{new_status}", "lead", id, actor.id)
        await self._db.commit()
        return updated

    async def convert(self, id: int, opts: ConvertLeadRequest, actor: CurrentUser) -> ConversionResult:
        lead = await self._repo.get_by_id(id)
        if lead is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Lead not found.")
        if lead.status == "converted":
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Lead already converted.")

        contact_id: int
        account_id: int | None = None
        deal_id: int | None = None

        # Create contact from lead
        from app.models.contact import Contact  # noqa: PLC0415
        contact = Contact(
            first_name=lead.first_name,
            last_name=lead.last_name,
            name=f"{lead.first_name} {lead.last_name}",
            email=lead.email,
            owner_id=lead.owner_id,
            created_by_id=actor.id,
        )
        self._db.add(contact)
        await self._db.flush()
        contact_id = contact.id

        await self._logger.log(self._db, "created_from_lead", "contact", contact_id, actor.id, {"lead_id": id})

        if opts.create_account and lead.company_name:
            from app.models.contact import Account  # noqa: PLC0415
            account = Account(name=lead.company_name, created_by_id=actor.id, owner_id=lead.owner_id)
            self._db.add(account)
            await self._db.flush()
            account_id = account.id
            contact.primary_account_id = account_id
            await self._logger.log(self._db, "created_from_lead", "account", account_id, actor.id)

        if opts.create_deal:
            await self._logger.log(
                self._db, "deal_stub_created", "lead", id, actor.id,
                {"deal_title": opts.deal_title, "deal_value": opts.deal_value}
            )
            deal_id = -1  # stub until Module 002 Deal integration

        await self._repo.update(id, {"status": "converted", "converted_contact_id": contact_id})
        await self._db.commit()

        return ConversionResult(contact_id=contact_id, account_id=account_id, deal_id=deal_id if deal_id and deal_id > 0 else None, lead_id=id)

    async def disqualify(self, id: int, reason: str, actor: CurrentUser) -> None:
        lead = await self._repo.get_by_id(id)
        if lead is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Lead not found.")
        await self._repo.update(id, {"status": "disqualified", "disqualify_reason": reason})
        await self._repo.archive(id, reason)
        await self._logger.log(self._db, "disqualified", "lead", id, actor.id)
        await self._db.commit()
