from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0014_user_language'
down_revision = '0013_picture_focus_area'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column('language', sa.String(8), nullable=False, server_default='en'),
    )


def downgrade():
    op.drop_column('users', 'language')
