"""blocks and mutes

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-01 16:30:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: str | None = 'e5f6a7b8c9d0'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _relation_table(name: str, left: str, right: str) -> None:
    op.create_table(
        name,
        sa.Column(left, sa.Uuid(), nullable=False),
        sa.Column(right, sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint([left], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint([right], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint(left, right),
    )
    op.create_index(op.f(f'ix_{name}_{right}'), name, [right], unique=False)


def upgrade() -> None:
    _relation_table('blocks', 'blocker_id', 'blocked_id')
    _relation_table('mutes', 'muter_id', 'muted_id')


def downgrade() -> None:
    op.drop_index(op.f('ix_mutes_muted_id'), table_name='mutes')
    op.drop_table('mutes')
    op.drop_index(op.f('ix_blocks_blocked_id'), table_name='blocks')
    op.drop_table('blocks')
