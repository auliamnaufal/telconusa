"""Initial CRM schema (Blueprint + Notulen PDF)

Revision ID: 0001_initial_crm
Revises:
Create Date: 2026-11-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_crm"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "coverage_areas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("city_code", sa.String(10), nullable=False),
        sa.Column("city_name", sa.String(60), nullable=False),
        sa.Column("district", sa.String(80), nullable=False),
        sa.Column("postal_code", sa.String(10), nullable=False, unique=True),
        sa.Column("is_covered", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "catalog_products",
        sa.Column("sku", sa.String(20), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("business_line", sa.String(15), nullable=False),
        sa.Column("unit_price", sa.BigInteger, nullable=False),
        sa.Column("billing_cycle", sa.String(20), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("speed_label", sa.String(40), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "campaigns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("campaign_code", sa.String(20), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("channel", sa.String(40), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "customers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_code", sa.String(20), nullable=False, unique=True),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(120), nullable=False, unique=True),
        sa.Column("whatsapp_number", sa.String(20), nullable=False),
        sa.Column("nik_or_npwp", sa.String(20), nullable=True, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("segment", sa.String(20), nullable=False, server_default="INDIVIDUAL"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "customer_install_addresses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("address_code", sa.String(20), nullable=False, unique=True),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("label", sa.String(60), nullable=False),
        sa.Column("install_address", sa.Text, nullable=False),
        sa.Column("city_code", sa.String(10), nullable=False),
        sa.Column("postal_code", sa.String(10), nullable=False),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("site_condition_notes", sa.Text, nullable=True),
    )
    op.create_table(
        "orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("order_no", sa.String(24), nullable=False, unique=True),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("install_address_id", sa.String(36), sa.ForeignKey("customer_install_addresses.id"), nullable=True),
        sa.Column("sku", sa.String(20), sa.ForeignKey("catalog_products.sku"), nullable=False),
        sa.Column("business_line", sa.String(15), nullable=False),
        sa.Column("sales_employee_id", sa.String(20), nullable=True),
        sa.Column("referral_code", sa.String(32), nullable=True),
        sa.Column("campaign_code", sa.String(20), nullable=True),
        sa.Column("subtotal", sa.BigInteger, nullable=False),
        sa.Column("discount", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("status", sa.String(24), nullable=False, server_default="SUBMITTED"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("subscription_code", sa.String(20), nullable=False, unique=True),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("install_address_id", sa.String(36), sa.ForeignKey("customer_install_addresses.id"), nullable=True),
        sa.Column("sku", sa.String(20), nullable=False),
        sa.Column("monthly_price", sa.BigInteger, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("activated_at", sa.DateTime, nullable=True),
    )
    op.create_table(
        "work_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("work_order_code", sa.String(20), nullable=False, unique=True),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("install_address_id", sa.String(36), sa.ForeignKey("customer_install_addresses.id"), nullable=True),
        sa.Column("technician_employee_id", sa.String(20), nullable=True),
        sa.Column("work_order_type", sa.String(20), nullable=False, server_default="INSTALLATION"),
        sa.Column("installation_status", sa.String(24), nullable=False, server_default="PENDING_ASSIGNMENT"),
        sa.Column("kit_id", sa.String(24), nullable=True),
        sa.Column("ont_serial_number", sa.String(40), nullable=True),
        sa.Column("cable_used_meters", sa.Integer, nullable=True),
        sa.Column("signal_dbm", sa.Numeric(5, 2), nullable=True),
        sa.Column("speedtest_mbps", sa.Numeric(6, 2), nullable=True),
        sa.Column("site_condition_notes", sa.Text, nullable=True),
        sa.Column("scheduled_date", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "tickets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("ticket_code", sa.String(20), nullable=False, unique=True),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("subscription_id", sa.String(36), nullable=True),
        sa.Column("priority", sa.String(4), nullable=False, server_default="P3"),
        sa.Column("subject", sa.String(160), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),
        sa.Column("assigned_technician_id", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "technician_ratings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("work_order_id", sa.String(36), sa.ForeignKey("work_orders.id"), nullable=False, unique=True),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("technician_employee_id", sa.String(20), nullable=False),
        sa.Column("rating_score", sa.Integer, nullable=False),
        sa.Column("rating_comment", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "processed_events",
        sa.Column("event_id", sa.String(40), primary_key=True),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("processed_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(60), nullable=False),
        sa.Column("correlation_id", sa.String(40), nullable=False),
        sa.Column("payload_json", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="SENT"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    for table in [
        "outbox_events", "processed_events", "technician_ratings", "tickets",
        "work_orders", "subscriptions", "orders", "customer_install_addresses",
        "customers", "campaigns", "catalog_products", "coverage_areas",
    ]:
        op.drop_table(table)
