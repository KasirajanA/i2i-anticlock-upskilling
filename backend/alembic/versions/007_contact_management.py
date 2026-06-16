"""Extend contacts/accounts; create contact_accounts, leads, segments, activity_log, custom_fields.

Revision ID: 007_contact_mgmt
Revises: 006_user_team_mgmt
Create Date: 2026-06-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "007_contact_mgmt"
down_revision = "006_user_team_mgmt"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend contacts table
    with op.batch_alter_table("contacts") as batch_op:
        batch_op.add_column(sa.Column("first_name", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("last_name", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("email", sa.String(254), nullable=True))
        batch_op.add_column(sa.Column("phone", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("job_title", sa.String(200), nullable=True))
        batch_op.add_column(sa.Column("primary_account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=True))
        batch_op.add_column(sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
        batch_op.add_column(sa.Column("tags", sa.JSON(), nullable=True, server_default="[]"))
        batch_op.add_column(sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="0"))

    op.create_index("ix_contacts_email", "contacts", ["email"], unique=True)

    # Extend accounts table
    with op.batch_alter_table("accounts") as batch_op:
        batch_op.add_column(sa.Column("industry", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("company_size", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("website", sa.String(500), nullable=True))
        batch_op.add_column(sa.Column("billing_address", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
        batch_op.add_column(sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True))
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))

    # New tables
    op.create_table(
        "contact_accounts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("contact_id", sa.Integer(), sa.ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("linked_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("contact_id", "account_id", name="uq_contact_accounts"),
    )

    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(254), nullable=True),
        sa.Column("company_name", sa.String(200), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="new"),
        sa.Column("disqualify_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("converted_contact_id", sa.Integer(), sa.ForeignKey("contacts.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_leads_status_owner", "leads", ["status", "owner_id"])
    op.create_index("ix_leads_email", "leads", ["email"])

    op.create_table(
        "segments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("filter_spec", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "contact_activity_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_contact_activity_entity", "contact_activity_log", ["entity_type", "entity_id", "created_at"])

    op.create_table(
        "custom_field_definitions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("field_key", sa.String(50), nullable=False, unique=True),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("field_type", sa.String(50), nullable=False),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("required", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "custom_field_values",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("definition_id", sa.Integer(), sa.ForeignKey("custom_field_definitions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("field_value", sa.Text(), nullable=True),
        sa.UniqueConstraint("definition_id", "entity_type", "entity_id", name="uq_cfv_def_entity"),
    )
    op.create_index("ix_cfv_entity", "custom_field_values", ["entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_table("custom_field_values")
    op.drop_table("custom_field_definitions")
    op.drop_table("contact_activity_log")
    op.drop_table("segments")
    op.drop_table("leads")
    op.drop_table("contact_accounts")
    op.drop_index("ix_contacts_email", table_name="contacts")
    with op.batch_alter_table("accounts") as batch_op:
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")
        batch_op.drop_column("created_by_id")
        batch_op.drop_column("owner_id")
        batch_op.drop_column("billing_address")
        batch_op.drop_column("website")
        batch_op.drop_column("company_size")
        batch_op.drop_column("industry")
    with op.batch_alter_table("contacts") as batch_op:
        batch_op.drop_column("is_archived")
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_by_id")
        batch_op.drop_column("tags")
        batch_op.drop_column("owner_id")
        batch_op.drop_column("primary_account_id")
        batch_op.drop_column("job_title")
        batch_op.drop_column("phone")
        batch_op.drop_column("email")
        batch_op.drop_column("last_name")
        batch_op.drop_column("first_name")
