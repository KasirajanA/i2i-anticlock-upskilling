from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str | None = None
    last_name: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    job_title: str | None = None
    primary_account_id: int | None = None
    owner_id: int | None = None
    tags: list = Field(default_factory=list)
    created_at: datetime
    deleted_at: datetime | None = None

    @property
    def display_name(self) -> str:
        if self.first_name or self.last_name:
            return f"{self.first_name or ''} {self.last_name or ''}".strip()
        return self.name or ""


class ContactDetailResponse(ContactResponse):
    custom_fields: list[dict] = Field(default_factory=list)


class CreateContactRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = None
    job_title: str | None = None
    account_ids: list[int] = Field(default_factory=list)
    primary_account_id: int | None = None
    tags: list[str] = Field(default_factory=list)
    owner_id: int | None = None


class UpdateContactRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = None
    job_title: str | None = None
    primary_account_id: int | None = None
    tags: list[str] | None = None
    owner_id: int | None = None


class DuplicateWarning(BaseModel):
    existing_id: int
    existing_email: str
    message: str = "A contact with this email already exists."


class ContactCreateResult(BaseModel):
    contact: ContactDetailResponse | None = None
    duplicate_warning: DuplicateWarning | None = None


class PaginatedContacts(BaseModel):
    items: list[ContactResponse]
    total: int
    next_cursor: str | None = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    industry: str | None = None
    company_size: str | None = None
    website: str | None = None
    owner_id: int | None = None
    created_at: datetime | None = None
    deleted_at: datetime | None = None


class AccountDetailResponse(AccountResponse):
    billing_address: str | None = None
    contact_count: int = 0


class CreateAccountRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    industry: str | None = None
    company_size: str | None = None
    website: str | None = None
    billing_address: str | None = None
    owner_id: int | None = None


class UpdateAccountRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    industry: str | None = None
    company_size: str | None = None
    website: str | None = None
    billing_address: str | None = None
    owner_id: int | None = None


class TimelineItem(BaseModel):
    type: str
    id: int
    label: str
    created_at: datetime


class PaginatedAccounts(BaseModel):
    items: list[AccountResponse]
    total: int
    next_cursor: str | None = None


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: str | None = None
    company_name: str | None = None
    status: str
    disqualify_reason: str | None = None
    notes: str | None = None
    owner_id: int | None = None
    converted_contact_id: int | None = None
    created_at: datetime


class CreateLeadRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str | None = None
    company_name: str | None = None
    notes: str | None = None
    owner_id: int | None = None


class UpdateLeadRequest(BaseModel):
    status: str | None = None
    disqualify_reason: str | None = None
    notes: str | None = None


class ConvertLeadRequest(BaseModel):
    create_account: bool = True
    create_deal: bool = False
    deal_title: str | None = None
    deal_value: float | None = None


class ConversionResult(BaseModel):
    contact_id: int
    account_id: int | None = None
    deal_id: int | None = None
    lead_id: int
    status: str = "converted"


class PaginatedLeads(BaseModel):
    items: list[LeadResponse]
    total: int


class SegmentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    entity_type: str
    filter_spec: dict = Field(default_factory=dict)


class SegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    entity_type: str
    filter_spec: dict = Field(default_factory=dict)
    live_count: int = 0
    created_at: datetime


class ImportResultResponse(BaseModel):
    imported: int
    skipped: int
    errors: int
    error_details: list[dict] = Field(default_factory=list)


class CustomFieldDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    field_key: str
    label: str
    field_type: str
    options: list | None = None
    required: bool


class CreateCustomFieldRequest(BaseModel):
    entity_type: str
    field_key: str = Field(min_length=3, max_length=50, pattern=r"^[a-z][a-z0-9_]{2,49}$")
    label: str = Field(min_length=1, max_length=200)
    field_type: str
    options: list[str] | None = None
    required: bool = False
