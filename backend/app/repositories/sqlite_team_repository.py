from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.team import Team, TeamMember


class SqliteTeamRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def create_team(
        self,
        name: str,
        lead_user_id: int | None,
        member_ids: list[int],
        created_by_id: int,
    ) -> Team:
        team = Team(name=name, lead_user_id=lead_user_id, created_by_id=created_by_id)
        self._db.add(team)
        await self._db.flush()  # populate team.id
        for uid in member_ids:
            self._db.add(TeamMember(team_id=team.id, user_id=uid))
        await self._db.commit()
        return await self._get_with_members(team.id)

    async def get_team(self, team_id: int) -> Team | None:
        return await self._get_with_members(team_id)

    async def list_teams(self) -> list[Team]:
        result = await self._db.execute(
            select(Team).options(selectinload(Team.members)).order_by(Team.created_at)
        )
        return list(result.scalars().all())

    async def update_team(
        self,
        team_id: int,
        name: str | None = None,
        lead_user_id: int | None = None,
    ) -> Team | None:
        team = await self._get_with_members(team_id)
        if team is None:
            return None
        if name is not None:
            team.name = name
        if lead_user_id is not None:
            team.lead_user_id = lead_user_id
        await self._db.commit()
        await self._db.refresh(team)
        return team

    async def add_members(self, team_id: int, user_ids: list[int]) -> None:
        existing = await self._db.execute(
            select(TeamMember.user_id).where(TeamMember.team_id == team_id)
        )
        existing_ids = {row[0] for row in existing}
        for uid in user_ids:
            if uid not in existing_ids:
                self._db.add(TeamMember(team_id=team_id, user_id=uid))
        await self._db.commit()

    async def remove_member(self, team_id: int, user_id: int) -> None:
        await self._db.execute(
            delete(TeamMember).where(
                TeamMember.team_id == team_id, TeamMember.user_id == user_id
            )
        )
        team = await self._db.get(Team, team_id)
        if team and team.lead_user_id == user_id:
            team.lead_user_id = None
        await self._db.commit()

    async def is_member(self, team_id: int, user_id: int) -> bool:
        result = await self._db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id, TeamMember.user_id == user_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def _get_with_members(self, team_id: int) -> Team | None:
        result = await self._db.execute(
            select(Team)
            .options(selectinload(Team.members))
            .where(Team.id == team_id)
        )
        return result.scalar_one_or_none()
