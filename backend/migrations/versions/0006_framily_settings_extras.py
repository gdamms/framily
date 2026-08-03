from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0006_framily_settings_extras'
down_revision = '0005_unique_email'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('framilies', sa.Column('resolution_width', sa.Integer, nullable=True))
    op.add_column('framilies', sa.Column('resolution_height', sa.Integer, nullable=True))
    op.add_column('framily_settings', sa.Column('orientation', sa.String(3), nullable=False, server_default='90'))
    op.add_column('framily_settings', sa.Column('interval_minutes', sa.Integer, nullable=False, server_default='5'))


def downgrade():
    op.drop_column('framily_settings', 'interval_minutes')
    op.drop_column('framily_settings', 'orientation')
    op.drop_column('framilies', 'resolution_height')
    op.drop_column('framilies', 'resolution_width')
