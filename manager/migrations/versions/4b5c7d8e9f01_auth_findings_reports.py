"""add users findings and reports

Revision ID: 4b5c7d8e9f01
Revises: 26fa71ddd354
"""
from alembic import op
import sqlalchemy as sa

revision = "4b5c7d8e9f01"
down_revision = "26fa71ddd354"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "findings",
        sa.Column("finding_id", sa.String(length=64), nullable=False),
        sa.Column("result_id", sa.String(length=64), nullable=False),
        sa.Column("agent_id", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.agent_id"]),
        sa.ForeignKeyConstraint(["result_id"], ["results.result_id"]),
        sa.PrimaryKeyConstraint("finding_id"),
    )
    op.create_table(
        "reports",
        sa.Column("report_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("report_type", sa.String(length=64), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=True),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("report_id"),
    )


def downgrade():
    op.drop_table("reports")
    op.drop_table("findings")
    op.drop_table("users")
