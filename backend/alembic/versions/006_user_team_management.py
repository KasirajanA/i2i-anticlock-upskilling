"""Add user profile fields; create teams and team_members tables.

Revision ID: 006_user_team_mgmt
Revises: 004_auth
Create Date: 2026-06-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "006_user_team_mgmt"
down_revision = "004_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("display_name", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("avatar_url", sa.String(300), nullable=True))
        batch_op.add_column(sa.Column("timezone", sa.String(100), nullable=True, server_default="UTC"))

    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("lead_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
    )

    op.create_table(
        "team_members",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_team_members_team_user", "team_members", ["team_id", "user_id"])


def downgrade() -> None:
    op.drop_table("team_members")
    op.drop_table("teams")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("timezone")
        batch_op.drop_column("avatar_url")
        batch_op.drop_column("display_name")
