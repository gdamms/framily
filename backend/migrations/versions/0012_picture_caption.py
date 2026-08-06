from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0012_picture_caption'
down_revision = '0011_membership_role_string'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'pictures',
        sa.Column('description', sa.String(300), nullable=True),
    )
    op.add_column(
        'framily_settings',
        sa.Column('show_caption', sa.Boolean, nullable=False, server_default=sa.true()),
    )


def downgrade():
    op.drop_column('framily_settings', 'show_caption')
    op.drop_column('pictures', 'description')
