"""add activity logs

Revision ID: 9b1a7f2e4c03
Revises: 5f0a2c9d7b31
Create Date: 2026-06-02 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b1a7f2e4c03"
down_revision: Union[str, Sequence[str], None] = "5f0a2c9d7b31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_name", sa.String(length=255), nullable=True),
        sa.Column("actor_email", sa.String(length=255), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_activity_logs_actor_email"), "activity_logs", ["actor_email"], unique=False)
    op.create_index(op.f("ix_activity_logs_actor_user_id"), "activity_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_activity_logs_created_at"), "activity_logs", ["created_at"], unique=False)
    op.create_index(op.f("ix_activity_logs_event_type"), "activity_logs", ["event_type"], unique=False)
    op.create_index(op.f("ix_activity_logs_id"), "activity_logs", ["id"], unique=False)
    op.create_index(op.f("ix_activity_logs_resource_id"), "activity_logs", ["resource_id"], unique=False)
    op.create_index(op.f("ix_activity_logs_resource_type"), "activity_logs", ["resource_type"], unique=False)
    op.create_index(op.f("ix_activity_logs_status"), "activity_logs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_activity_logs_status"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_resource_type"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_resource_id"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_id"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_event_type"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_created_at"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_actor_user_id"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_actor_email"), table_name="activity_logs")
    op.drop_table("activity_logs")
