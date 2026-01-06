"""add_is_active_to_user

Revision ID: 5da339e1e27f
Revises: 4ca339e1e27f
Create Date: 2026-01-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5da339e1e27f'
down_revision: Union[str, None] = '4ca339e1e27f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True))
    # Set existing users to active
    op.execute("UPDATE users SET is_active = 't'")
    op.alter_column('users', 'is_active', nullable=False)


def downgrade() -> None:
    op.drop_column('users', 'is_active')
