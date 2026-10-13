"""automation_rules

Revision ID: 0cf1c6efdcaa
Revises: 571c1412ac65
Create Date: 2026-10-01 11:53:35.042917

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0cf1c6efdcaa"
down_revision: Union[str, Sequence[str], None] = "571c1412ac65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "automation_rules",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "strategy_key",
            sa.String(length=32),
            server_default=sa.text("'conservative'"),
            nullable=False,
        ),
        sa.Column(
            "parameters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "uq_automation_rules_location_id",
        "automation_rules",
        ["location_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_automation_rules_location_id",
        table_name="automation_rules",
    )
    op.drop_table("automation_rules")