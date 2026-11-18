"""seed default tags

Revision ID: 535e4d189f90
Revises: 24e65caf78e8
Create Date: 2026-11-15 12:53:34.183948

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '535e4d189f90'
down_revision: Union[str, Sequence[str], None] = '24e65caf78e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_TAGS = ["Marketing", "Social", "Personal", "Work", "News"]

# A lightweight snapshot of the tags table, as it looks at this point in history.
tags_table = sa.table(
    "tags",
    sa.column("id", sa.Integer),
    sa.column("name", sa.String),
)


def upgrade() -> None:
    """Seed the default tags."""
    op.bulk_insert(tags_table, [{"name": name} for name in DEFAULT_TAGS])


def downgrade() -> None:
    """Remove the default tags."""
    op.execute(tags_table.delete().where(tags_table.c.name.in_(DEFAULT_TAGS)))