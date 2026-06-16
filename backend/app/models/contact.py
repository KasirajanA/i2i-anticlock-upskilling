"""Contact, Account, Lead, Segment, and related models for Module 007."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Backward-compat column used by ticket_service for contact_name_snapshot
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Module 007 proper fields
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    primary_account_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("accounts.id"), nullable=True
    )
    owner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Backward compat: soft-archive boolean used by existing code
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    @property
    def display_name(self) -> str:
        if self.first_name or self.last_name:
            return f"{self.first_name or ''} {self.last_name or ''}".strip()
        return self.name or ""

    account_links: Mapped[list["ContactAccount"]] = relationship(
        "ContactAccount", back_populates="contact", cascade="all, delete-orphan"
    )


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    billing_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Backward compat
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    contacts_linked: Mapped[list["ContactAccount"]] = relationship(
        "ContactAccount", back_populates="account"
    )


class ContactAccount(Base):
    """Many-to-many link between contacts and accounts."""

    __tablename__ = "contact_accounts"
    __table_args__ = (UniqueConstraint("contact_id", "account_id", name="uq_contact_accounts"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contact_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    linked_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    contact: Mapped["Contact"] = relationship("Contact", back_populates="account_links")
    account: Mapped["Account"] = relationship("Account", back_populates="contacts_linked")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="new")
    disqualify_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    converted_contact_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("contacts.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    filter_spec: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    owner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ContactActivityLog(Base):
    """Generic activity log for contacts/accounts/leads."""

    __tablename__ = "contact_activity_log"
    __table_args__ = (
        Index("ix_contact_activity_entity", "entity_type", "entity_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class CustomFieldDefinition(Base):
    __tablename__ = "custom_field_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    field_key: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    values: Mapped[list["CustomFieldValue"]] = relationship(
        "CustomFieldValue", back_populates="definition"
    )


class CustomFieldValue(Base):
    __tablename__ = "custom_field_values"
    __table_args__ = (
        UniqueConstraint("definition_id", "entity_type", "entity_id", name="uq_cfv_def_entity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    definition_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("custom_field_definitions.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    field_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    definition: Mapped["CustomFieldDefinition"] = relationship(
        "CustomFieldDefinition", back_populates="values"
    )
