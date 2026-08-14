"""add unique constraint on assignment application_id, fix cascade ownership

Revision ID: 5927a1e1d7fd
Revises: 61d15deeae16
Create Date: 2026-08-14 09:25:16.314603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5927a1e1d7fd'
down_revision: Union[str, Sequence[str], None] = '61d15deeae16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('ix_campaign_assignments_application_id_uq', 'campaign_assignments', ['application_id'], unique=True)
    op.drop_index('ix_campaign_assignments_application_id', table_name='campaign_assignments')
    op.execute("ALTER TABLE campaign_assignments RENAME INDEX ix_campaign_assignments_application_id_uq TO ix_campaign_assignments_application_id")
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.create_index('ix_campaign_assignments_application_id_nu', 'campaign_assignments', ['application_id'], unique=False)
    op.drop_index('ix_campaign_assignments_application_id', table_name='campaign_assignments')
    op.execute("ALTER TABLE campaign_assignments RENAME INDEX ix_campaign_assignments_application_id_nu TO ix_campaign_assignments_application_id")
    # ### end Alembic commands ###
