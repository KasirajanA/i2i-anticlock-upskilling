"""Create contracts, contract_attachments, activity_logs, renewal_links tables.

Revision ID: 001_contracts
Revises: 000_prereqs
Create Date: 2026-06-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_contracts"
down_revision: Union[str, None] = "000_prereqs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contracts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ref_id", sa.String(10), nullable=False, unique=True),
        sa.Column("value", sa.Numeric(15, 2), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "Draft",
                "Sent for Review",
                "Active",
                "Expired",
                "Terminated",
                name="contractstatus",
            ),
            nullable=False,
            server_default="Draft",
        ),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_renewal_due", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "account_id", sa.Integer, sa.ForeignKey("accounts.id"), nullable=False
        ),
        sa.Column(
            "deal_id", sa.Integer, sa.ForeignKey("deals.id"), nullable=True
        ),
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
        sa.CheckConstraint("end_date >= start_date", name="ck_contracts_dates"),
    )
    op.create_index("ix_contracts_status", "contracts", ["status"])
    op.create_index("ix_contracts_owner_id", "contracts", ["owner_id"])
    op.create_index("ix_contracts_account_id", "contracts", ["account_id"])
    op.create_index("ix_contracts_end_date", "contracts", ["end_date"])
    op.create_index("ix_contracts_status_end_date", "contracts", ["status", "end_date"])
    op.create_index("ix_contracts_is_archived", "contracts", ["is_archived"])

    op.create_table(
        "contract_attachments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "contract_id",
            sa.Integer,
            sa.ForeignKey("contracts.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("filename", sa.Text, nullable=False),
        sa.Column("mime_type", sa.Text, nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.CheckConstraint("size_bytes <= 1048576", name="ck_attachment_size"),
        sa.UniqueConstraint("contract_id", name="uq_attachment_contract"),
    )

    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "contract_id",
            sa.Integer,
            sa.ForeignKey("contracts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action_type", sa.Text, nullable=False),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
    )
    op.create_index("ix_activity_logs_contract_id", "activity_logs", ["contract_id"])

    op.create_table(
        "renewal_links",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "original_contract_id",
            sa.Integer,
            sa.ForeignKey("contracts.id"),
            nullable=False,
        ),
        sa.Column(
            "successor_contract_id",
            sa.Integer,
            sa.ForeignKey("contracts.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
    )
    op.create_index(
        "ix_renewal_links_original_id", "renewal_links", ["original_contract_id"]
    )


def downgrade() -> None:
    op.drop_table("renewal_links")
    op.drop_index("ix_activity_logs_contract_id", table_name="activity_logs")
    op.drop_table("activity_logs")
    op.drop_table("contract_attachments")
    op.drop_index("ix_contracts_is_archived", table_name="contracts")
    op.drop_index("ix_contracts_status_end_date", table_name="contracts")
    op.drop_index("ix_contracts_end_date", table_name="contracts")
    op.drop_index("ix_contracts_account_id", table_name="contracts")
    op.drop_index("ix_contracts_owner_id", table_name="contracts")
    op.drop_index("ix_contracts_status", table_name="contracts")
    op.drop_table("contracts")
