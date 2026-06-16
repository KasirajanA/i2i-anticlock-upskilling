"""Abstract repository interfaces for the Customer Support module."""

from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.support import SLARecord, Ticket


class ITicketRepository(ABC):
    """Abstract interface — enables dependency inversion and easy test doubles."""

    @abstractmethod
    async def create(
        self,
        session: AsyncSession,
        ticket: Ticket,
        sla: SLARecord,
    ) -> tuple[Ticket, SLARecord]:
        ...

    @abstractmethod
    async def get_by_id(
        self, session: AsyncSession, ticket_id: int
    ) -> tuple[Ticket, SLARecord | None] | None:
        ...

    @abstractmethod
    async def list_paginated(
        self,
        session: AsyncSession,
        *,
        queue: str | None = None,
        caller_id: int | None = None,
        status: str | None = None,
        priority: str | None = None,
        assignee_id: int | None = None,
        account_id: int | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[tuple[Ticket, SLARecord | None]], str | None, int]:
        ...

    @abstractmethod
    async def update(self, session: AsyncSession, ticket: Ticket) -> Ticket:
        ...

    @abstractmethod
    async def assign(
        self, session: AsyncSession, ticket: Ticket, assignee_id: int | None
    ) -> Ticket:
        ...
