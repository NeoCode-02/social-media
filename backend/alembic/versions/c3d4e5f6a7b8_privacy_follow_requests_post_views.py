"""private accounts, follow requests, post views

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-01 12:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: str | None = 'b2c3d4e5f6a7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Private accounts.
    op.add_column(
        'users',
        sa.Column('is_private', sa.Boolean(), server_default=sa.false(), nullable=False),
    )

    # Follow request lifecycle: existing rows are all already-accepted follows.
    op.add_column(
        'follows',
        sa.Column('status', sa.String(length=16), server_default='accepted', nullable=False),
    )
    op.create_index(op.f('ix_follows_status'), 'follows', ['status'], unique=False)

    # Per-viewer post impressions.
    op.create_table(
        'post_views',
        sa.Column('post_id', sa.Uuid(), nullable=False),
        sa.Column('viewer_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['viewer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('post_id', 'viewer_id'),
    )
    op.create_index(op.f('ix_post_views_post_id'), 'post_views', ['post_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_post_views_post_id'), table_name='post_views')
    op.drop_table('post_views')
    op.drop_index(op.f('ix_follows_status'), table_name='follows')
    op.drop_column('follows', 'status')
    op.drop_column('users', 'is_private')
