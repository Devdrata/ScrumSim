"""add srs_intake agent type enum value

Revision ID: 8246106c712c
Revises: cfa0ea88bf91
Create Date: 2026-08-13 05:21:00.618472

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8246106c712c'
down_revision: Union[str, None] = 'cfa0ea88bf91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE agent_type ADD VALUE IF NOT EXISTS 'SRS_INTAKE'")


def downgrade() -> None:
    # Postgres has no DROP VALUE for enums; leaving the label in place on downgrade is harmless.
    pass
