"""add token_usage and source columns

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-14

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("token_usage", postgresql.JSONB(), nullable=True))
    op.add_column("articles", sa.Column("source", sa.Text(), nullable=False, server_default="local"))


def downgrade() -> None:
    op.drop_column("articles", "source")
    op.drop_column("articles", "token_usage")
