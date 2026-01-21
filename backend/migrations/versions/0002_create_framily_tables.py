from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_create_framily_tables'
down_revision = '0001_create_users'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to users table
    op.add_column('users', sa.Column('display_name', sa.String(100), nullable=False, server_default='unknown'))
    op.add_column('users', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))

    # Remove unique constraint on email (email may not be unique per README)
    op.drop_index('ix_users_email', table_name='users')
    op.create_index('ix_users_email', 'users', ['email'], unique=False)

    # Create framilies table
    op.create_table(
        'framilies',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('code', sa.String(8), unique=True, index=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False, server_default='unknown'),
        sa.Column('frame_token', sa.String(64), unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create framily_settings table
    op.create_table(
        'framily_settings',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('framily_id', sa.Integer, sa.ForeignKey('framilies.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('picture_duration', sa.Integer, default=10),
        sa.Column('shuffle_mode', sa.String(20), default='random'),
        sa.Column('transition_effect', sa.String(20), default='fade'),
        sa.Column('overlays', sa.JSON, default=[]),
    )

    # Create memberships table
    op.create_table(
        'memberships',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('framily_id', sa.Integer, sa.ForeignKey('framilies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.Integer, default=0, nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'framily_id', name='unique_user_framily'),
    )

    # Create pictures table
    op.create_table(
        'pictures',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('framily_id', sa.Integer, sa.ForeignKey('framilies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('uploaded_by', sa.Integer, sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('upload_date', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('metadata', sa.JSON, default={}),
    )


def downgrade():
    op.drop_table('pictures')
    op.drop_table('memberships')
    op.drop_table('framily_settings')
    op.drop_table('framilies')

    # Remove new columns from users table
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'display_name')

    # Restore unique constraint on email
    op.drop_index('ix_users_email', table_name='users')
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
