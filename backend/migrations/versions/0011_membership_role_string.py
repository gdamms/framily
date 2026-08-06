from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0011_membership_role_string'
down_revision = '0010_preprocess_level'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'memberships',
        'role',
        existing_type=sa.Integer(),
        type_=sa.String(10),
        existing_nullable=False,
        postgresql_using="CASE role WHEN 0 THEN 'invited' WHEN 1 THEN 'member' WHEN 2 THEN 'admin' END",
    )


def downgrade():
    op.alter_column(
        'memberships',
        'role',
        existing_type=sa.String(10),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using="CASE role WHEN 'invited' THEN 0 WHEN 'member' THEN 1 WHEN 'admin' THEN 2 END",
    )
