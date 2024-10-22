"""Add PR campaign fields and update existing structure

Revision ID: 38e9996a0ce7
Revises: d12fbf00eade
Create Date: 2024-10-16 21:35:48.211743

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError

# revision identifiers, used by Alembic.
revision = '38e9996a0ce7'
down_revision = 'd12fbf00eade'
branch_labels = None
depends_on = None

def upgrade():
    # Create author table if it doesn't exist
    try:
        op.create_table('author',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('website_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(['website_id'], ['website.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
    except OperationalError:
        pass  # Table already exists

    # Add author_id to outreach_attempt table
    with op.batch_alter_table('outreach_attempt', schema=None) as batch_op:
        try:
            batch_op.add_column(sa.Column('author_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key('fk_outreach_attempt_author', 'author', ['author_id'], ['id'])
        except OperationalError:
            pass  # Column or constraint might already exist

def downgrade():
    # Remove author_id from outreach_attempt table
    with op.batch_alter_table('outreach_attempt', schema=None) as batch_op:
        batch_op.drop_constraint('fk_outreach_attempt_author', type_='foreignkey')
        batch_op.drop_column('author_id')

    # We don't drop the author table in downgrade to prevent data loss
    # If you want to drop it, uncomment the following line:
    # op.drop_table('author')
