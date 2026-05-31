"""posts, follows, likes (twitter half)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-31 18:30:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: str | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'posts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('author_id', sa.Uuid(), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.Uuid(), nullable=True),
        sa.Column('repost_of_id', sa.Uuid(), nullable=True),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['posts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['repost_of_id'], ['posts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_posts_author_id'), 'posts', ['author_id'], unique=False)
    op.create_index(op.f('ix_posts_parent_id'), 'posts', ['parent_id'], unique=False)
    op.create_index(op.f('ix_posts_repost_of_id'), 'posts', ['repost_of_id'], unique=False)
    op.create_index('ix_posts_author_id_id', 'posts', ['author_id', 'id'], unique=False)

    op.create_table(
        'likes',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('post_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'post_id'),
    )
    op.create_index(op.f('ix_likes_post_id'), 'likes', ['post_id'], unique=False)

    op.create_table(
        'follows',
        sa.Column('follower_id', sa.Uuid(), nullable=False),
        sa.Column('followee_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['followee_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['follower_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('follower_id', 'followee_id'),
    )
    op.create_index(op.f('ix_follows_followee_id'), 'follows', ['followee_id'], unique=False)

    # attachments can now belong to a post instead of a chat message.
    op.alter_column('attachments', 'chat_id', existing_type=sa.Uuid(), nullable=True)
    op.add_column('attachments', sa.Column('post_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_attachments_post_id'), 'attachments', ['post_id'], unique=False)
    op.create_foreign_key(
        'fk_attachments_post_id_posts', 'attachments', 'posts',
        ['post_id'], ['id'], ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('fk_attachments_post_id_posts', 'attachments', type_='foreignkey')
    op.drop_index(op.f('ix_attachments_post_id'), table_name='attachments')
    op.drop_column('attachments', 'post_id')
    op.alter_column('attachments', 'chat_id', existing_type=sa.Uuid(), nullable=False)

    op.drop_index(op.f('ix_follows_followee_id'), table_name='follows')
    op.drop_table('follows')
    op.drop_index(op.f('ix_likes_post_id'), table_name='likes')
    op.drop_table('likes')
    op.drop_index('ix_posts_author_id_id', table_name='posts')
    op.drop_index(op.f('ix_posts_repost_of_id'), table_name='posts')
    op.drop_index(op.f('ix_posts_parent_id'), table_name='posts')
    op.drop_index(op.f('ix_posts_author_id'), table_name='posts')
    op.drop_table('posts')
