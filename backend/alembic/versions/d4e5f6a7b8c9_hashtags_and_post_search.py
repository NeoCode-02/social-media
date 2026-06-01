"""hashtags + post full-text search index

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-01 14:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: str | None = 'c3d4e5f6a7b8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'post_hashtags',
        sa.Column('post_id', sa.Uuid(), nullable=False),
        sa.Column('tag', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('post_id', 'tag'),
    )
    op.create_index(op.f('ix_post_hashtags_tag'), 'post_hashtags', ['tag'], unique=False)
    op.create_index(
        'ix_post_hashtags_created_at', 'post_hashtags', ['created_at'], unique=False
    )

    # Trigram GIN index so `text ILIKE '%q%'` post search stays indexed.
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    op.create_index(
        'ix_posts_text_trgm',
        'posts',
        ['text'],
        unique=False,
        postgresql_using='gin',
        postgresql_ops={'text': 'gin_trgm_ops'},
    )


def downgrade() -> None:
    op.drop_index('ix_posts_text_trgm', table_name='posts', postgresql_using='gin')
    op.drop_index('ix_post_hashtags_created_at', table_name='post_hashtags')
    op.drop_index(op.f('ix_post_hashtags_tag'), table_name='post_hashtags')
    op.drop_table('post_hashtags')
