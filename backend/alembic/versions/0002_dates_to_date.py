"""Store the three complaint dates as real DATE columns instead of text.

Revision ID: 0002_dates_to_date
Revises: 0001_initial
"""
import sqlalchemy as sa

from alembic import op

revision = "0002_dates_to_date"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

DATE_COLUMNS = ["manufacturing_date", "expiry_date", "complaint_date"]


def upgrade() -> None:
    for col in DATE_COLUMNS:
        # Existing text is converted only if it is already YYYY-MM-DD.
        # Anything else (blank, "June 2025", typos) becomes NULL instead of
        # making the whole migration fail.
        op.alter_column(
            "complaints", col,
            type_=sa.Date(),
            existing_type=sa.String(20),
            postgresql_using=(
                f"CASE WHEN {col} ~ '^\\d{{4}}-\\d{{2}}-\\d{{2}}$' "
                f"THEN {col}::date ELSE NULL END"
            ),
        )


def downgrade() -> None:
    for col in DATE_COLUMNS:
        op.alter_column(
            "complaints", col,
            type_=sa.String(20),
            existing_type=sa.Date(),
            postgresql_using=f"to_char({col}, 'YYYY-MM-DD')",
        )
