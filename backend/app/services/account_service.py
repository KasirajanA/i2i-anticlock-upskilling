from __future__ import annotations

import asyncio

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.models.contact import Contact
from app.repositories.sqlite_account_repository import SqliteAccountRepository
from app.schemas.contact import (
    AccountDetailResponse,
    PaginatedAccounts,
    TimelineItem,
)
from app.services.contact_activity_logger import ContactActivityLogger


class AccountService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session
        self._repo = SqliteAccountRepository(session)
        self._logger = ContactActivityLogger()

    async def create(self, data: dict, actor: CurrentUser):
        data.setdefault("created_by_id", actor.id)
        account = await self._repo.create(data)
        await self._logger.log(self._db, "created", "account", account.id, actor.id)
        await self._db.commit()
        return account

    async def get(self, id: int) -> AccountDetailResponse:
        account = await self._repo.get_by_id(id)
        if account is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found.")
        count = await self._repo.get_contact_count(id)
        detail = AccountDetailResponse.model_validate(account)
        detail.contact_count = count
        return detail

    async def list(
        self,
        q: str | None = None,
        industry: str | None = None,
        owner_id: int | None = None,
        include_archived: bool = False,
        cursor: str | None = None,
        limit: int = 50,
    ) -> PaginatedAccounts:
        return await self._repo.list(
            q=q,
            industry=industry,
            owner_id=owner_id,
            include_archived=include_archived,
            cursor=cursor,
            limit=limit,
        )

    async def update(self, id: int, data: dict, actor: CurrentUser):
        account = await self._repo.get_by_id(id)
        if account is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found.")
        updated = await self._repo.update(id, data)
        await self._logger.log(self._db, "updated", "account", id, actor.id)
        await self._db.commit()
        return updated

    async def archive(self, id: int, actor: CurrentUser) -> None:
        account = await self._repo.get_by_id(id)
        if account is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Account not found.")
        await self._repo.archive(id)
        await self._logger.log(self._db, "archived", "account", id, actor.id)
        await self._db.commit()

    async def get_timeline(self, account_id: int) -> list[TimelineItem]:
        async def _contacts():
            result = await self._db.execute(
                select(Contact).where(Contact.primary_account_id == account_id)
            )
            contacts = result.scalars().all()
            return [
                TimelineItem(
                    type="contact",
                    id=c.id,
                    label=f"Contact: {c.display_name or c.email or str(c.id)}",
                    created_at=c.created_at,
                )
                for c in contacts
            ]

        # Stub: deals and tickets from other modules return empty lists for now
        async def _deals():
            return []

        async def _tickets():
            return []

        contacts_items, deal_items, ticket_items = await asyncio.gather(
            _contacts(), _deals(), _tickets()
        )
        all_items = contacts_items + deal_items + ticket_items
        all_items.sort(key=lambda x: x.created_at, reverse=True)
        return all_items
