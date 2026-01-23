from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003_add_profile_picture'
down_revision = '0002_create_framily_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Remove url column from pictures table (URL is now computed from picture_id)
    op.drop_column('pictures', 'url')


def downgrade():
    # Add url column back to pictures table
    op.add_column('pictures', sa.Column('url', sa.String(500), nullable=True))
