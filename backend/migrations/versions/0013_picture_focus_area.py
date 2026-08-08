from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0013_picture_focus_area'
down_revision = '0012_picture_caption'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'pictures',
        sa.Column('focus_area', sa.JSON, nullable=True),
    )


def downgrade():
    op.drop_column('pictures', 'focus_area')
