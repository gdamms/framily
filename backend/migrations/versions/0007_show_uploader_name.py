from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0007_show_uploader_name'
down_revision = '0006_framily_settings_extras'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'framily_settings',
        sa.Column('show_uploader_name', sa.Boolean, nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column('framily_settings', 'show_uploader_name')
