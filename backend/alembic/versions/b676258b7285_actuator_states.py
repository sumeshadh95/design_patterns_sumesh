"""actuator_states

Revision ID: b676258b7285
Revises: 0cf1c6efdcaa
Create Date: 2026-10-13 14:42:49.948673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b676258b7285'
down_revision: Union[str, Sequence[str], None] = '0cf1c6efdcaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('actuator_states',
    sa.Column('device_id', sa.UUID(), nullable=False),
    sa.Column('state', sa.String(length=32), server_default=sa.text("'idle'"), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('device_id')
    )

    # Seed: every actuator that already exists starts in the idle state.
    op.execute(
        """
        INSERT INTO actuator_states (device_id, state)
        SELECT id, 'idle' FROM devices WHERE role = 'actuator'
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('actuator_states')
