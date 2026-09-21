"""add agent runtime columns

Revision ID: 7c2d4e6f8a10
Revises: 4b5c7d8e9f01
"""

from alembic import op
import sqlalchemy as sa


revision = "7c2d4e6f8a10"
down_revision = "4b5c7d8e9f01"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("agents")}

    if "version" not in columns:
        op.add_column(
            "agents",
            sa.Column("version", sa.String(length=32), nullable=True, server_default="1.0.0"),
        )
    if "capabilities" not in columns:
        op.add_column(
            "agents",
            sa.Column("capabilities", sa.Text(), nullable=True, server_default="[]"),
        )
    if "registered_at" not in columns:
        op.add_column("agents", sa.Column("registered_at", sa.DateTime(), nullable=True))
    if "current_job" not in columns:
        op.add_column("agents", sa.Column("current_job", sa.String(length=64), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("agents")}

    for column_name in ("current_job", "registered_at", "capabilities", "version"):
        if column_name in columns:
            op.drop_column("agents", column_name)
