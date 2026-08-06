from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0009_show_date'
down_revision = '0008_frame_ip_and_dead_columns'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'framily_settings',
        sa.Column('show_date', sa.Boolean, nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column('framily_settings', 'show_date')
