from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.repositories.sqlite_contact_repository import SqliteContactRepository
from app.schemas.contact import (
    ContactCreateResult,
    ContactDetailResponse,
    DuplicateWarning,
    PaginatedContacts,
)
from app.services.contact_activity_logger import ContactActivityLogger
from app.services.custom_field_service import CustomFieldService


class ContactService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session
        self._repo = SqliteContactRepository(session)
        self._logger = ContactActivityLogger()
        self._cf = CustomFieldService(session)

    async def create(self, data: dict, actor: CurrentUser) -> ContactCreateResult:
        email = (data.get("email") or "").lower().strip()
        if email:
            existing = await self._repo.find_by_email(email)
            if existing:
                warning = DuplicateWarning(existing_id=existing.id, existing_email=existing.email or "")
                return ContactCreateResult(duplicate_warning=warning)

        account_ids = data.pop("account_ids", [])
        # Normalize name for backward compat
        if "first_name" in data and "last_name" in data:
            data.setdefault("name", f"{data['first_name']} {data['last_name']}")
        if email:
            data["email"] = email

        contact = await self._repo.create(data, account_ids)
        await self._logger.log(self._db, "created", "contact", contact.id, actor.id)

        custom_fields = await self._cf.get_values("contact", contact.id)
        detail = ContactDetailResponse.model_validate(contact)
        detail.custom_fields = custom_fields
        return ContactCreateResult(contact=detail)

    async def get(self, id: int) -> ContactDetailResponse:
        contact = await self._repo.get_by_id(id)
        if contact is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Contact not found.")
        detail = ContactDetailResponse.model_validate(contact)
        detail.custom_fields = await self._cf.get_values("contact", id)
        return detail

    async def list(
        self,
        q: str | None = None,
        account_id: int | None = None,
        tag: str | None = None,
        owner_id: int | None = None,
        include_archived: bool = False,
        cursor: str | None = None,
        limit: int = 50,
    ) -> PaginatedContacts:
        return await self._repo.list(
            q=q,
            account_id=account_id,
            tag=tag,
            owner_id=owner_id,
            include_archived=include_archived,
            cursor=cursor,
            limit=limit,
        )

    async def update(self, id: int, data: dict, actor: CurrentUser):
        contact = await self._repo.get_by_id(id)
        if contact is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Contact not found.")
        updated = await self._repo.update(id, data)
        await self._logger.log(self._db, "updated", "contact", id, actor.id)
        return updated

    async def archive(self, id: int, actor: CurrentUser) -> None:
        contact = await self._repo.get_by_id(id)
        if contact is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Contact not found.")
        await self._repo.archive(id)
        await self._logger.log(self._db, "archived", "contact", id, actor.id)
