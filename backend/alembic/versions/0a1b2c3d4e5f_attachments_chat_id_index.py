"""index attachments(chat_id, created_at)

Revision ID: 0a1b2c3d4e5f
Revises: 9c0d1e2f3a4b
Create Date: 2026-06-02 22:00:00.000000

"""
from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0a1b2c3d4e5f'
down_revision: str | None = '9c0d1e2f3a4b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        'ix_attachments_chat_id_created_at',
        'attachments',
        ['chat_id', 'created_at'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_attachments_chat_id_created_at', table_name='attachments')
