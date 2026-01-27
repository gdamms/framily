from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004_picture_visibility'
down_revision = '0003_add_profile_picture'
branch_labels = None
depends_on = None


def upgrade():
    # Create picture_visibility junction table for many-to-many relationship
    op.create_table(
        'picture_visibility',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('picture_id', sa.String(36), sa.ForeignKey('pictures.id', ondelete='CASCADE'), nullable=False),
        sa.Column('framily_id', sa.Integer, sa.ForeignKey('framilies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('picture_id', 'framily_id', name='unique_picture_framily_visibility'),
    )

    # Remove framily_id foreign key from pictures table (picture is no longer tied to a single framily)
    op.drop_constraint('pictures_framily_id_fkey', 'pictures', type_='foreignkey')
    op.drop_column('pictures', 'framily_id')


def downgrade():
    # Add framily_id back to pictures table
    op.add_column('pictures', sa.Column('framily_id', sa.Integer, nullable=True))
    op.create_foreign_key('pictures_framily_id_fkey', 'pictures', 'framilies', ['framily_id'], ['id'], ondelete='CASCADE')

    # Drop picture_visibility table
    op.drop_table('picture_visibility')
