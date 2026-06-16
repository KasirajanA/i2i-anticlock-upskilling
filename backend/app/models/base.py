"""Prerequisite stub models shared across CRM modules.

Stubs will be superseded (extended, not replaced) when their owning modules land:
  - users / user_sessions  → Module 005 (Authentication) + 006 (User Management)
  - accounts / contacts    → Module 007 (Contact Management)
  - notifications          → Module 008 (Notifications)
  - deals                  → Module 002 (Sales Pipeline) — full model in models/deal.py
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(100), nullable=True, default="UTC")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=True, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )



class Notification(Base):
    """Stub — will be superseded by Module 008 (Notifications)."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class UserSession(Base):
    """HTTP-only session store — Module 005 (Authentication)."""

    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class FailedLoginAttempt(Base):
    """Tracks consecutive failed logins for account lockout."""

    __tablename__ = "failed_login_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_attempt_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    locked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
