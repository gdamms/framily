from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0005_unique_email'
down_revision = '0004_picture_visibility'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint('uq_users_email', 'users', ['email'])


def downgrade():
    op.drop_constraint('uq_users_email', 'users', type_='unique')
