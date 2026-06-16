"""Create sales pipeline tables: replace stub deals, add deal_comments,
deal_activity_log, contacts stub, and notifications stub.

Revision ID: 002_pipeline
Revises: 001_contracts
Create Date: 2026-06-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_pipeline"
down_revision: Union[str, None] = "001_contracts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add contacts stub (FK target for deals.contact_id)
    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default="0"),
    )

    # Add notifications stub (written by scheduler overdue job)
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.Integer, nullable=True),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
    )

    # Replace stub deals table with full Sales Pipeline schema.
    # SQLite does not support ALTER TABLE column additions, so we drop + recreate.
    # The contracts.deal_id FK is declarative-only (SQLite does not enforce FKs
    # by default), so existing contract rows are unaffected.
    op.drop_table("deals")
    op.create_table(
        "deals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ref_id", sa.String(12), unique=True, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("value", sa.Numeric(15, 2), nullable=False, server_default="0.00"),
        sa.Column("stage", sa.String(20), nullable=False),
        sa.Column("expected_close_date", sa.Date, nullable=False),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("contact_id", sa.Integer, sa.ForeignKey("contacts.id"), nullable=True),
        sa.Column("loss_reason", sa.Text, nullable=True),
        sa.Column("is_overdue", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
    )
    op.create_index("idx_deals_owner_stage",         "deals", ["owner_id", "stage"])
    op.create_index("idx_deals_stage",               "deals", ["stage"])
    op.create_index("idx_deals_expected_close_date", "deals", ["expected_close_date"])
    op.create_index("idx_deals_is_overdue",          "deals", ["is_overdue"])
    op.create_index("idx_deals_account_id",          "deals", ["account_id"])
    op.create_index("idx_deals_ref_id",              "deals", ["ref_id"], unique=True)

    # Deal comments
    op.create_table(
        "deal_comments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("deal_id", sa.Integer, sa.ForeignKey("deals.id"), nullable=False),
        sa.Column("author_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
    )
    op.create_index("idx_deal_comments_deal_id", "deal_comments", ["deal_id"])

    # Deal activity log
    op.create_table(
        "deal_activity_log",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("deal_id", sa.Integer, sa.ForeignKey("deals.id"), nullable=False),
        sa.Column("action_type", sa.String(40), nullable=False),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
    )
    op.create_index("idx_deal_activity_deal_id", "deal_activity_log", ["deal_id"])


def downgrade() -> None:
    op.drop_table("deal_activity_log")
    op.drop_table("deal_comments")
    op.drop_index("idx_deals_ref_id",              table_name="deals")
    op.drop_index("idx_deals_account_id",          table_name="deals")
    op.drop_index("idx_deals_is_overdue",          table_name="deals")
    op.drop_index("idx_deals_expected_close_date", table_name="deals")
    op.drop_index("idx_deals_stage",               table_name="deals")
    op.drop_index("idx_deals_owner_stage",         table_name="deals")
    op.drop_table("deals")
    # Restore stub deals table
    op.create_table(
        "deals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default="0"),
    )
    op.drop_table("notifications")
    op.drop_table("contacts")
