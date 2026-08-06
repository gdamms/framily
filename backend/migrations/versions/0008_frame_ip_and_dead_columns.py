from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0008_frame_ip_and_dead_columns'
down_revision = '0007_show_uploader_name'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('framilies', sa.Column('ip_address', sa.String(45), nullable=True))

    op.drop_column('framily_settings', 'picture_duration')
    op.drop_column('framily_settings', 'shuffle_mode')
    op.drop_column('framily_settings', 'transition_effect')
    op.drop_column('framily_settings', 'overlays')


def downgrade():
    op.add_column('framily_settings', sa.Column('overlays', sa.JSON, default=[]))
    op.add_column('framily_settings', sa.Column('transition_effect', sa.String(20), default='fade'))
    op.add_column('framily_settings', sa.Column('shuffle_mode', sa.String(20), default='random'))
    op.add_column('framily_settings', sa.Column('picture_duration', sa.Integer, default=10))

    op.drop_column('framilies', 'ip_address')
