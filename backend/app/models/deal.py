"""Sales Pipeline ORM models: DealStage, Deal, DealComment, DealActivity."""

import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DealStage(str, enum.Enum):
    LEAD_IN     = "Lead In"
    QUALIFIED   = "Qualified"
    PROPOSAL    = "Proposal"
    NEGOTIATION = "Negotiation"
    CLOSED_WON  = "Closed Won"
    CLOSED_LOST = "Closed Lost"

    @property
    def is_terminal(self) -> bool:
        return self in (DealStage.CLOSED_WON, DealStage.CLOSED_LOST)

    @classmethod
    def probability(cls, stage: "DealStage") -> Decimal:
        return {
            cls.LEAD_IN:     Decimal("0.10"),
            cls.QUALIFIED:   Decimal("0.25"),
            cls.PROPOSAL:    Decimal("0.50"),
            cls.NEGOTIATION: Decimal("0.75"),
            cls.CLOSED_WON:  Decimal("1.00"),
            cls.CLOSED_LOST: Decimal("0.00"),
        }[stage]


class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = (
        Index("idx_deals_owner_stage", "owner_id", "stage"),
        Index("idx_deals_stage", "stage"),
        Index("idx_deals_expected_close_date", "expected_close_date"),
        Index("idx_deals_is_overdue", "is_overdue"),
        Index("idx_deals_account_id", "account_id"),
        Index("idx_deals_ref_id", "ref_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ref_id: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    stage: Mapped[DealStage] = mapped_column(
        Enum(DealStage, name="dealstage", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    expected_close_date: Mapped[date] = mapped_column(Date, nullable=False)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    account_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=True)
    contact_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("contacts.id"), nullable=True)
    loss_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_overdue: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    # Relationships (lazy — eagerly loaded per-query via selectinload in repository)
    owner   = relationship("User",    foreign_keys=[owner_id],   lazy="select")
    account = relationship("Account", foreign_keys=[account_id], lazy="select")
    contact = relationship("Contact", foreign_keys=[contact_id], lazy="select")
    comments = relationship("DealComment", back_populates="deal", lazy="select")
    activity = relationship(
        "DealActivity",
        back_populates="deal",
        order_by="DealActivity.created_at",
        lazy="select",
    )


class DealComment(Base):
    __tablename__ = "deal_comments"
    __table_args__ = (
        Index("idx_deal_comments_deal_id", "deal_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_id: Mapped[int] = mapped_column(Integer, ForeignKey("deals.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    deal   = relationship("Deal", back_populates="comments")
    author = relationship("User", foreign_keys=[author_id], lazy="select")


class DealActivity(Base):
    __tablename__ = "deal_activity_log"
    __table_args__ = (
        Index("idx_deal_activity_deal_id", "deal_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_id: Mapped[int] = mapped_column(Integer, ForeignKey("deals.id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(40), nullable=False)
    actor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    deal  = relationship("Deal", back_populates="activity")
    actor = relationship("User", foreign_keys=[actor_id], lazy="select")
