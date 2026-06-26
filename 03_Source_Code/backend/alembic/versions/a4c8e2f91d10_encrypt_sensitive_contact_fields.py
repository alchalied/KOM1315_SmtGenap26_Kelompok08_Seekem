"""encrypt sensitive contact fields

Revision ID: a4c8e2f91d10
Revises: 9b1a7f2e4c03
Create Date: 2026-06-03 00:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4c8e2f91d10"
down_revision: Union[str, Sequence[str], None] = "9b1a7f2e4c03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "phone",
        existing_type=sa.String(length=20),
        type_=sa.String(length=512),
        existing_nullable=False,
    )
    op.alter_column(
        "klaim",
        "contact",
        existing_type=sa.String(length=255),
        type_=sa.String(length=512),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "klaim",
        "contact",
        existing_type=sa.String(length=512),
        type_=sa.String(length=255),
        existing_nullable=True,
    )
    op.alter_column(
        "users",
        "phone",
        existing_type=sa.String(length=512),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
