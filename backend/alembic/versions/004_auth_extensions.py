"""Add auth columns to users/user_sessions; add failed_login_attempts.

Revision ID: 004_auth
Revises: 003_support
Create Date: 2026-06-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "004_auth"
down_revision = "003_support"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add auth columns to users
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("password_hash", sa.String(200), nullable=True))
        batch_op.add_column(sa.Column("locked", sa.Boolean(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()))

    # Add last_active_at to user_sessions
    with op.batch_alter_table("user_sessions") as batch_op:
        batch_op.add_column(sa.Column("last_active_at", sa.DateTime(), nullable=True, server_default=sa.func.now()))

    # Create failed_login_attempts table
    op.create_table(
        "failed_login_attempts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(254), unique=True, nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_attempt_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("locked_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("failed_login_attempts")
    with op.batch_alter_table("user_sessions") as batch_op:
        batch_op.drop_column("last_active_at")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("locked")
        batch_op.drop_column("password_hash")
