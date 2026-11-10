"""Initial schema: the complaints table as it was before Day 3.

Revision ID: 0001_initial
Revises:
"""
import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "complaints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("complaint_number", sa.String(30), unique=True),
        sa.Column("complaint_source", sa.String(100)),
        sa.Column("customer_name", sa.String(200)),
        sa.Column("product_name", sa.String(200)),
        sa.Column("product_strength", sa.String(100)),
        sa.Column("batch_number", sa.String(100)),
        sa.Column("manufacturing_date", sa.String(20)),
        sa.Column("expiry_date", sa.String(20)),
        sa.Column("quantity_affected", sa.String(50)),
        sa.Column("complaint_type", sa.String(100)),
        sa.Column("complaint_date", sa.String(20)),
        sa.Column("complaint_description", sa.Text()),
        sa.Column("initial_severity", sa.String(20)),
        sa.Column("priority", sa.String(20)),
        sa.Column("ai_risk_level", sa.String(20)),
        sa.Column("ai_risk_score", sa.Integer()),
        sa.Column("ai_risk_rationale", sa.Text()),
        sa.Column("source_text", sa.Text()),
        sa.Column("status", sa.String(30)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_complaints_batch_number", "complaints", ["batch_number"])


def downgrade() -> None:
    op.drop_index("ix_complaints_batch_number", table_name="complaints")
    op.drop_table("complaints")
