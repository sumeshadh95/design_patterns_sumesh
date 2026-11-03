"""device_zone_assignment

Revision ID: c3a1d5e7f902
Revises: b676258b7285
Create Date: 2026-11-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3a1d5e7f902'
down_revision: Union[str, Sequence[str], None] = 'b676258b7285'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('devices', sa.Column('zone_id', sa.UUID(), nullable=True))
    op.add_column('devices', sa.Column('location_id', sa.UUID(), nullable=True))
    op.create_index('ix_devices_zone_id', 'devices', ['zone_id'], unique=False)
    op.create_index('ix_devices_location_id', 'devices', ['location_id'], unique=False)
    op.create_foreign_key(
        'fk_devices_zone_id_zones', 'devices', 'zones',
        ['zone_id'], ['id'], ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_devices_location_id_locations', 'devices', 'locations',
        ['location_id'], ['id'], ondelete='SET NULL',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_devices_location_id_locations', 'devices', type_='foreignkey')
    op.drop_constraint('fk_devices_zone_id_zones', 'devices', type_='foreignkey')
    op.drop_index('ix_devices_location_id', table_name='devices')
    op.drop_index('ix_devices_zone_id', table_name='devices')
    op.drop_column('devices', 'location_id')
    op.drop_column('devices', 'zone_id')
