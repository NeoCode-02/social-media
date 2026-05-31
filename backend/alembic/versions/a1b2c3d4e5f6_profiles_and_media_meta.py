"""profiles and richer media metadata

Revision ID: a1b2c3d4e5f6
Revises: 9516e5d0e298
Create Date: 2026-05-31 16:30:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: str | None = '9516e5d0e298'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # users: profile fields
    op.add_column('users', sa.Column('bio', sa.String(length=280), nullable=True))
    op.add_column('users', sa.Column('location', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('website', sa.String(length=255), nullable=True))

    # attachments: audio/video duration + render hints
    op.add_column('attachments', sa.Column('duration_ms', sa.Integer(), nullable=True))
    op.add_column(
        'attachments',
        sa.Column('as_file', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        'attachments',
        sa.Column('is_voice', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # Drop the server defaults; the ORM supplies the value going forward.
    op.alter_column('attachments', 'as_file', server_default=None)
    op.alter_column('attachments', 'is_voice', server_default=None)


def downgrade() -> None:
    op.drop_column('attachments', 'is_voice')
    op.drop_column('attachments', 'as_file')
    op.drop_column('attachments', 'duration_ms')
    op.drop_column('users', 'website')
    op.drop_column('users', 'location')
    op.drop_column('users', 'bio')
