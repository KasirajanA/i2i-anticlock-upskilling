from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user
from app.schemas.contact import (
    ContactCreateResult,
    ContactDetailResponse,
    CreateContactRequest,
    ImportResultResponse,
    PaginatedContacts,
    UpdateContactRequest,
)
from app.services.contact_service import ContactService
from app.services.csv_importer import CSVImporter

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=PaginatedContacts)
async def list_contacts(
    q: str | None = None,
    account_id: int | None = None,
    tag: str | None = None,
    owner_id: int | None = None,
    include_archived: bool = False,
    cursor: str | None = None,
    limit: int = 50,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PaginatedContacts:
    svc = ContactService(session)
    return await svc.list(q=q, account_id=account_id, tag=tag, owner_id=owner_id,
                           include_archived=include_archived, cursor=cursor, limit=limit)


@router.post("", response_model=ContactCreateResult, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: CreateContactRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ContactCreateResult:
    if current_user.role == "Support Agent":
        from fastapi import HTTPException  # noqa: PLC0415
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Access denied.")
    svc = ContactService(session)
    data = payload.model_dump()
    return await svc.create(data, current_user)


@router.get("/{contact_id}", response_model=ContactDetailResponse)
async def get_contact(
    contact_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ContactDetailResponse:
    svc = ContactService(session)
    return await svc.get(contact_id)


@router.patch("/{contact_id}", response_model=ContactDetailResponse)
async def update_contact(
    contact_id: int,
    payload: UpdateContactRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ContactDetailResponse:
    svc = ContactService(session)
    data = payload.model_dump(exclude_none=True)
    contact = await svc.update(contact_id, data, current_user)
    return ContactDetailResponse.model_validate(contact)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_contact(
    contact_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if current_user.role not in ("Admin",):
        from fastapi import HTTPException  # noqa: PLC0415
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Admin only.")
    svc = ContactService(session)
    await svc.archive(contact_id, current_user)


@router.post("/import", response_model=ImportResultResponse)
async def import_contacts(
    file: UploadFile = File(...),
    duplicate_mode: str = Form(default="skip"),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ImportResultResponse:
    if current_user.role not in ("Admin", "Sales Rep"):
        from fastapi import HTTPException  # noqa: PLC0415
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Access denied.")
    importer = CSVImporter(session)
    return await importer.import_file(file, duplicate_mode)
