"""removed unique constraint agent non-deleted address

Revision ID: e0d8421619c2
Revises: e404f52562c2
Create Date: 2021-06-28 08:04:42.333490

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'e0d8421619c2'
down_revision = 'e404f52562c2'
branch_labels = None
depends_on = None


def upgrade():
    with op.get_context().autocommit_block():
        try:
            op.drop_index('ix_agents_address_not_deleted', table_name='agents')
        except Exception:
            pass


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_agents_address_not_deleted', 'agents', ['address'], unique=True)
    # ### end Alembic commands ###
