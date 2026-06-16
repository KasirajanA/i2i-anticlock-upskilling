from datetime import date, datetime
from decimal import Decimal
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ContractStatus(str, PyEnum):
    DRAFT = "Draft"
    SENT_FOR_REVIEW = "Sent for Review"
    ACTIVE = "Active"
    EXPIRED = "Expired"
    TERMINATED = "Terminated"


class Contract(Base):
    __tablename__ = "contracts"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_contracts_dates"),
        Index("ix_contracts_status", "status"),
        Index("ix_contracts_owner_id", "owner_id"),
        Index("ix_contracts_account_id", "account_id"),
        Index("ix_contracts_end_date", "end_date"),
        Index("ix_contracts_status_end_date", "status", "end_date"),
        Index("ix_contracts_is_archived", "is_archived"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ref_id: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ContractStatus] = mapped_column(
        Enum(ContractStatus), nullable=False, default=ContractStatus.DRAFT
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_renewal_due: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("accounts.id"), nullable=False
    )
    deal_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("deals.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    attachment: Mapped["ContractAttachment | None"] = relationship(
        "ContractAttachment",
        back_populates="contract",
        uselist=False,
        cascade="all, delete-orphan",
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog",
        back_populates="contract",
        order_by="ActivityLog.created_at.desc()",
    )
    renewal_as_original: Mapped["RenewalLink | None"] = relationship(
        "RenewalLink",
        foreign_keys="RenewalLink.original_contract_id",
        back_populates="original_contract",
        uselist=False,
    )
    renewal_as_successor: Mapped["RenewalLink | None"] = relationship(
        "RenewalLink",
        foreign_keys="RenewalLink.successor_contract_id",
        back_populates="successor_contract",
        uselist=False,
    )


class ContractAttachment(Base):
    __tablename__ = "contract_attachments"
    __table_args__ = (
        CheckConstraint("size_bytes <= 1048576", name="ck_attachment_size"),
        UniqueConstraint("contract_id", name="uq_attachment_contract"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    contract: Mapped["Contract"] = relationship(
        "Contract", back_populates="attachment"
    )


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    __table_args__ = (
        Index("ix_activity_logs_contract_id", "contract_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    contract: Mapped["Contract"] = relationship(
        "Contract", back_populates="activity_logs"
    )


class RenewalLink(Base):
    __tablename__ = "renewal_links"
    __table_args__ = (
        Index("ix_renewal_links_original_id", "original_contract_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    original_contract_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contracts.id"), nullable=False
    )
    successor_contract_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("contracts.id"),
        nullable=False,
        unique=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    original_contract: Mapped["Contract"] = relationship(
        "Contract",
        foreign_keys=[original_contract_id],
        back_populates="renewal_as_original",
    )
    successor_contract: Mapped["Contract"] = relationship(
        "Contract",
        foreign_keys=[successor_contract_id],
        back_populates="renewal_as_successor",
    )
