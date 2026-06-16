"""Create prerequisite tables: users, accounts, deals, user_sessions.

These stubs provide FK targets for the Contract module. Each will be
extended (not replaced) by its owning module.

Revision ID: 000_prereqs
Revises:
Create Date: 2026-06-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "000_prereqs"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(200), nullable=False, unique=True),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
    )

    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default="0"),
    )

    op.create_table(
        "deals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default="0"),
    )

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
    )


def downgrade() -> None:
    op.drop_table("user_sessions")
    op.drop_table("deals")
    op.drop_table("accounts")
    op.drop_table("users")
