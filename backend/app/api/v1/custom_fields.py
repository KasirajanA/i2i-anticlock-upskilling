from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user
from app.dependencies.role_guard import require_module_access
from app.schemas.contact import CreateCustomFieldRequest, CustomFieldDefinitionResponse
from app.services.custom_field_service import CustomFieldService

router = APIRouter(prefix="/custom-fields", tags=["custom-fields"])

_require_admin = require_module_access("user_team_management")


@router.get("", response_model=list[CustomFieldDefinitionResponse])
async def list_custom_fields(
    entity_type: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[CustomFieldDefinitionResponse]:
    svc = CustomFieldService(session)
    if entity_type is None:
        entity_type = "contact"
    defns = await svc.list_definitions(entity_type)
    return [CustomFieldDefinitionResponse.model_validate(d) for d in defns]


@router.post("", response_model=CustomFieldDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_field(
    payload: CreateCustomFieldRequest,
    current_user: CurrentUser = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
) -> CustomFieldDefinitionResponse:
    svc = CustomFieldService(session)
    defn = await svc.create_definition(
        entity_type=payload.entity_type,
        field_key=payload.field_key,
        label=payload.label,
        field_type=payload.field_type,
        options=payload.options,
        required=payload.required,
        created_by_id=current_user.id,
    )
    return CustomFieldDefinitionResponse.model_validate(defn)
