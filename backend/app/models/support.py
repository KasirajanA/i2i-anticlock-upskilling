"""ORM models for the Customer Support module (Module 003)."""

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        Index("idx_tickets_status_created", "status", "created_at"),
        Index("idx_tickets_assignee_status", "assignee_id", "status"),
        Index("idx_tickets_contact_id", "contact_id"),
        Index("idx_tickets_seq_number", "seq_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seq_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(TicketStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TicketStatus.OPEN.value,
    )
    priority: Mapped[str] = mapped_column(
        Enum(TicketPriority, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    contact_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("contacts.id"), nullable=True
    )
    contact_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    account_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("accounts.id"), nullable=True
    )
    assignee_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    created_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    sla_records: Mapped[list["SLARecord"]] = relationship(
        "SLARecord", back_populates="ticket", lazy="select"
    )
    replies: Mapped[list["Reply"]] = relationship(
        "Reply", back_populates="ticket", lazy="select"
    )
    activity_log: Mapped[list["TicketActivityLog"]] = relationship(
        "TicketActivityLog", back_populates="ticket", lazy="select"
    )


class Reply(Base):
    __tablename__ = "replies"
    __table_args__ = (Index("idx_replies_ticket_created", "ticket_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tickets.id"), nullable=False
    )
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="replies")


class SLARecord(Base):
    __tablename__ = "sla_records"
    __table_args__ = (
        Index("idx_sla_ticket_active", "ticket_id", "is_active"),
        Index("idx_sla_first_response_due", "first_response_due"),
        Index("idx_sla_resolution_due", "resolution_due"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tickets.id"), nullable=False
    )
    cycle: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_response_due: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    resolution_due: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    first_response_breached: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    resolution_breached: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="sla_records")


class TicketActivityLog(Base):
    __tablename__ = "ticket_activity_log"
    __table_args__ = (
        Index("idx_ticket_activity_ticket_created", "ticket_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tickets.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="activity_log")


class TicketSequence(Base):
    __tablename__ = "ticket_sequence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    next_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
