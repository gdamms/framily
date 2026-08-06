from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0010_preprocess_level'
down_revision = '0009_show_date'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'framily_settings',
        sa.Column('preprocess_level', sa.Integer, nullable=False, server_default='50'),
    )


def downgrade():
    op.drop_column('framily_settings', 'preprocess_level')
