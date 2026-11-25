"""Baseline tables: id counters, outbox, dead letters, processed events

Revision ID: 0001_baseline_tables
Revises:
Create Date: 2026-11-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_baseline_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "id_counters",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value", sa.BigInteger, nullable=False, server_default="0"),
    )
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_id", sa.String(40), nullable=False, unique=True),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("correlation_id", sa.String(40), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("payload_json", sa.Text, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime, nullable=False),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "dead_letter_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_id", sa.String(40), nullable=False),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("correlation_id", sa.String(40), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("payload_json", sa.Text, nullable=False),
        sa.Column("attempts", sa.Integer, nullable=False),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column("dead_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "processed_events",
        sa.Column("event_id", sa.String(40), primary_key=True),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("processed_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("processed_events")
    op.drop_table("dead_letter_events")
    op.drop_table("outbox_events")
    op.drop_table("id_counters")
