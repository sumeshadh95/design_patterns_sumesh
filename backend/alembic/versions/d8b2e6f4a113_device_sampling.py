"""device_sampling

Revision ID: d8b2e6f4a113
Revises: c3a1d5e7f902
Create Date: 2026-11-03 12:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8b2e6f4a113'
down_revision: Union[str, Sequence[str], None] = 'c3a1d5e7f902'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'devices',
        sa.Column(
            'sampling_interval_seconds',
            sa.Integer(),
            server_default=sa.text('300'),
            nullable=False,
        ),
    )
    op.add_column(
        'devices',
        sa.Column(
            'tracking_enabled',
            sa.Boolean(),
            server_default=sa.text('true'),
            nullable=False,
        ),
    )

    # Backfill: the interval moves from default_config JSON to the column.
    op.execute(
        """
        UPDATE devices
        SET sampling_interval_seconds =
            GREATEST((default_config->>'sampling_interval_seconds')::int, 5)
        WHERE jsonb_typeof(default_config->'sampling_interval_seconds') = 'number'
        """
    )

    # Protocol values used by the adapter selector: simulation | mqtt.
    op.execute(
        """
        UPDATE devices
        SET default_config = jsonb_set(default_config, '{protocol}', '"simulation"')
        WHERE default_config->>'protocol' IS NULL
           OR default_config->>'protocol' = 'sim'
        """
    )
    op.execute(
        """
        UPDATE devices
        SET default_config = jsonb_set(default_config, '{protocol}', '"mqtt"')
        WHERE default_config->>'protocol' = 'gpio-stub'
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('devices', 'tracking_enabled')
    op.drop_column('devices', 'sampling_interval_seconds')
