"""add image_plan column

Revision ID: 0001
Revises:
Create Date: 2026-05-13

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("articles", sa.Column("image_plan", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("articles", "image_plan")
