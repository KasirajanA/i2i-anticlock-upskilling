"""Create customer support tables: tickets, ticket_sequence, replies,
sla_records, ticket_activity_log.

Revision ID: 003_support
Revises: 002_pipeline
Create Date: 2026-06-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_support"
down_revision: Union[str, None] = "002_pipeline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ticket_sequence",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("next_value", sa.Integer, nullable=False, server_default="1"),
    )
    # Seed the single sequence row
    op.execute("INSERT INTO ticket_sequence (id, next_value) VALUES (1, 1)")

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("seq_number", sa.Integer, nullable=False, unique=True),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(10), nullable=False),
        sa.Column("contact_id", sa.Integer, sa.ForeignKey("contacts.id"), nullable=True),
        sa.Column("contact_name_snapshot", sa.String(255), nullable=False),
        sa.Column("account_id", sa.Integer, sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("assignee_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )
    op.create_index("idx_tickets_status_created", "tickets", ["status", "created_at"])
    op.create_index("idx_tickets_assignee_status", "tickets", ["assignee_id", "status"])
    op.create_index("idx_tickets_contact_id", "tickets", ["contact_id"])
    op.create_index("idx_tickets_seq_number", "tickets", ["seq_number"])

    op.create_table(
        "replies",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ticket_id", sa.Integer, sa.ForeignKey("tickets.id"), nullable=False),
        sa.Column("author_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("is_internal", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_replies_ticket_created", "replies", ["ticket_id", "created_at"])

    op.create_table(
        "sla_records",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ticket_id", sa.Integer, sa.ForeignKey("tickets.id"), nullable=False),
        sa.Column("cycle", sa.Integer, nullable=False, server_default="1"),
        sa.Column("first_response_due", sa.DateTime, nullable=False),
        sa.Column("resolution_due", sa.DateTime, nullable=False),
        sa.Column("first_response_at", sa.DateTime, nullable=True),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
        sa.Column("first_response_breached", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("resolution_breached", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_sla_ticket_active", "sla_records", ["ticket_id", "is_active"])
    op.create_index("idx_sla_first_response_due", "sla_records", ["first_response_due"])
    op.create_index("idx_sla_resolution_due", "sla_records", ["resolution_due"])

    op.create_table(
        "ticket_activity_log",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ticket_id", sa.Integer, sa.ForeignKey("tickets.id"), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "idx_ticket_activity_ticket_created",
        "ticket_activity_log",
        ["ticket_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("ticket_activity_log")
    op.drop_table("sla_records")
    op.drop_table("replies")
    op.drop_table("tickets")
    op.drop_table("ticket_sequence")
