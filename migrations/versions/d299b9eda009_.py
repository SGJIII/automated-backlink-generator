"""empty message

Revision ID: d299b9eda009
Revises: 64abf066597c
Create Date: 2024-10-08 11:01:20.783873

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'd299b9eda009'
down_revision = '64abf066597c'
branch_labels = None
depends_on = None


def upgrade():
    # Create an inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # Check if 'author' table doesn't exist
    if 'author' not in tables:
        op.create_table('author',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('website_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(['website_id'], ['website.id'], ),
        sa.PrimaryKeyConstraint('id')
        )

    # Check if 'author_id' column exists in 'outreach_attempt' table
    columns = [col['name'] for col in inspector.get_columns('outreach_attempt')]
    if 'author_id' not in columns:
        with op.batch_alter_table('outreach_attempt', schema=None) as batch_op:
            batch_op.add_column(sa.Column('author_id', sa.Integer(), nullable=True))

    # Create a default author for each website if it doesn't exist
    op.execute("""
    INSERT INTO author (website_id, name, email)
    SELECT DISTINCT website_id, 'Default Author', 'default@example.com'
    FROM outreach_attempt
    WHERE website_id NOT IN (SELECT DISTINCT website_id FROM author)
    """)

    # Update existing rows to set author_id
    op.execute("""
    UPDATE outreach_attempt
    SET author_id = (
        SELECT id 
        FROM author 
        WHERE author.website_id = outreach_attempt.website_id 
        LIMIT 1
    )
    WHERE author_id IS NULL
    """)

    # Now make author_id non-nullable and add the foreign key constraint
    with op.batch_alter_table('outreach_attempt', schema=None) as batch_op:
        batch_op.alter_column('author_id', nullable=False)
        batch_op.create_foreign_key('fk_outreach_attempt_author', 'author', ['author_id'], ['id'])

def downgrade():
    with op.batch_alter_table('outreach_attempt', schema=None) as batch_op:
        batch_op.drop_constraint('fk_outreach_attempt_author', type_='foreignkey')
        batch_op.drop_column('author_id')

    op.drop_table('author')
