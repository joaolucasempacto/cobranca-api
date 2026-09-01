"""create charges

Revision ID: c4d8e1f2a6b9
Revises: a9c4e2f7b1d6
Create Date: 2026-09-01 11:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c4d8e1f2a6b9"
down_revision: Union[str, Sequence[str], None] = "a9c4e2f7b1d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "charges",
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "paid",
                "overdue",
                "cancelled",
                name="charge_status_enum",
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_charges_amount_positive"),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_charges_customer_id"),
        "charges",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_charges_due_date"),
        "charges",
        ["due_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_charges_status"),
        "charges",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_charges_status"), table_name="charges")
    op.drop_index(op.f("ix_charges_due_date"), table_name="charges")
    op.drop_index(op.f("ix_charges_customer_id"), table_name="charges")
    op.drop_table("charges")
    postgresql.ENUM(
        "pending",
        "paid",
        "overdue",
        "cancelled",
        name="charge_status_enum",
    ).drop(op.get_bind(), checkfirst=True)
