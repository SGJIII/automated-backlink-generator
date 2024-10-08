"""Add page_authority to Website model

Revision ID: cb72bf733cd1
Revises: ca5a5673bdd1
Create Date: 2024-10-05 16:23:55.634579

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cb72bf733cd1'
down_revision = 'ca5a5673bdd1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('website', schema=None) as batch_op:
        batch_op.add_column(sa.Column('page_authority', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('website', schema=None) as batch_op:
        batch_op.drop_column('page_authority')

    # ### end Alembic commands ###
