"""add audit log signatures

Revision ID: b7d9e1c0a245
Revises: a4c8e2f91d10
Create Date: 2026-06-03 01:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7d9e1c0a245"
down_revision: Union[str, Sequence[str], None] = "a4c8e2f91d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("signature_algorithm", sa.String(length=50), nullable=True))
    op.add_column("audit_logs", sa.Column("signature", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("audit_logs", "signature")
    op.drop_column("audit_logs", "signature_algorithm")
