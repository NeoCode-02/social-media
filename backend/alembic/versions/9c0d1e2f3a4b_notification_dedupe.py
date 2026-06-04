"""dedupe mention notifications and enforce uniqueness

Revision ID: 9c0d1e2f3a4b
Revises: a7b8c9d0e1f2
Create Date: 2026-06-02 21:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c0d1e2f3a4b'
down_revision: str | None = 'a7b8c9d0e1f2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Dedupe pre-existing mention notifications: keep the oldest row per
    # (recipient, actor, post) and delete the rest. This is the precondition
    # for the unique index below.
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            DELETE FROM notifications n
            WHERE n.type = 'mention'
              AND n.id NOT IN (
                -- Postgres has no MIN(uuid) aggregate; the UUIDv7 text form
                -- sorts chronologically, so MIN over ::text picks the oldest.
                SELECT MIN(id::text)::uuid FROM notifications
                WHERE type = 'mention'
                GROUP BY recipient_id, actor_id, post_id
              )
            """
        )
    )
    op.create_index(
        'uq_notifications_mention',
        'notifications',
        ['recipient_id', 'actor_id', 'post_id'],
        unique=True,
        postgresql_where=sa.text("type = 'mention'"),
    )


def downgrade() -> None:
    op.drop_index('uq_notifications_mention', table_name='notifications')
