from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.repositories.sqlite_team_repository import SqliteTeamRepository


class TeamService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = SqliteTeamRepository(session)

    async def create_team(
        self,
        name: str,
        lead_user_id: int | None,
        member_ids: list[int],
        created_by: int,
    ) -> Team:
        if lead_user_id is not None and lead_user_id not in member_ids:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="lead_user_id must be in member_ids.",
            )
        return await self._repo.create_team(name, lead_user_id, member_ids, created_by)

    async def get_team(self, team_id: int) -> Team:
        team = await self._repo.get_team(team_id)
        if team is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found.")
        return team

    async def list_teams(self) -> list[Team]:
        return await self._repo.list_teams()

    async def update_team(
        self,
        team_id: int,
        name: str | None = None,
        lead_user_id: int | None = None,
    ) -> Team:
        team = await self._repo.get_team(team_id)
        if team is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found.")
        if lead_user_id is not None:
            if not await self._repo.is_member(team_id, lead_user_id):
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="lead_user_id must be a member of the team.",
                )
        result = await self._repo.update_team(team_id, name=name, lead_user_id=lead_user_id)
        return result  # type: ignore[return-value]

    async def add_members(self, team_id: int, user_ids: list[int]) -> None:
        team = await self._repo.get_team(team_id)
        if team is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found.")
        await self._repo.add_members(team_id, user_ids)

    async def remove_member(self, team_id: int, user_id: int) -> None:
        team = await self._repo.get_team(team_id)
        if team is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Team not found.")
        await self._repo.remove_member(team_id, user_id)
