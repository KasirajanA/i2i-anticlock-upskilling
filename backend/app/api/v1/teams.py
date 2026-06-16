from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser
from app.dependencies.role_guard import require_module_access
from app.schemas.user_mgmt import (
    AddMembersRequest,
    CreateTeamRequest,
    PaginatedTeams,
    TeamDetailResponse,
    TeamMemberResponse,
    TeamResponse,
    UpdateTeamRequest,
)
from app.services.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["teams"])

_require_admin = require_module_access("user_team_management")


def _team_to_response(team) -> TeamResponse:
    return TeamResponse(
        id=team.id,
        name=team.name,
        lead_user_id=team.lead_user_id,
        created_by_id=team.created_by_id,
        created_at=team.created_at,
        member_count=len(team.members),
    )


def _team_to_detail(team) -> TeamDetailResponse:
    return TeamDetailResponse(
        id=team.id,
        name=team.name,
        lead_user_id=team.lead_user_id,
        created_by_id=team.created_by_id,
        created_at=team.created_at,
        member_count=len(team.members),
        members=[TeamMemberResponse(user_id=m.user_id, joined_at=m.joined_at) for m in team.members],
    )


@router.get("", response_model=PaginatedTeams)
async def list_teams(
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
) -> PaginatedTeams:
    svc = TeamService(session)
    teams = await svc.list_teams()
    return PaginatedTeams(items=[_team_to_response(t) for t in teams], total=len(teams))


@router.post("", response_model=TeamDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    payload: CreateTeamRequest,
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
) -> TeamDetailResponse:
    svc = TeamService(session)
    team = await svc.create_team(
        name=payload.name,
        lead_user_id=payload.lead_user_id,
        member_ids=payload.member_ids,
        created_by=current_user.id,
    )
    return _team_to_detail(team)


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: int,
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
) -> TeamDetailResponse:
    svc = TeamService(session)
    team = await svc.get_team(team_id)
    return _team_to_detail(team)


@router.patch("/{team_id}", response_model=TeamDetailResponse)
async def update_team(
    team_id: int,
    payload: UpdateTeamRequest,
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
) -> TeamDetailResponse:
    svc = TeamService(session)
    team = await svc.update_team(team_id, name=payload.name, lead_user_id=payload.lead_user_id)
    return _team_to_detail(team)


@router.post("/{team_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def add_members(
    team_id: int,
    payload: AddMembersRequest,
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = TeamService(session)
    await svc.add_members(team_id, payload.user_ids)


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    team_id: int,
    user_id: int,
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
):
    svc = TeamService(session)
    await svc.remove_member(team_id, user_id)
