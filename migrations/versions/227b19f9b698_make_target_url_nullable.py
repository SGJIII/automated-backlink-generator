"""Make target_url nullable

Revision ID: 227b19f9b698
Revises: 38e9996a0ce7
Create Date: 2024-10-22 11:26:40.023560

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError


# revision identifiers, used by Alembic.
revision = '227b19f9b698'
down_revision = '38e9996a0ce7'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the temporary table if it exists
    try:
        op.execute('DROP TABLE IF EXISTS _alembic_tmp_campaign')
    except Exception as e:
        print(f"Error dropping temporary table: {e}")

    # Proceed with the migration
    with op.batch_alter_table('campaign', schema=None) as batch_op:
        # Set default values for existing rows
        batch_op.execute("UPDATE campaign SET campaign_type = 'seo' WHERE campaign_type IS NULL")
        
        # Alter columns
        batch_op.alter_column('campaign_type',
               existing_type=sa.VARCHAR(length=50),
               nullable=False,
               server_default='seo')
        batch_op.alter_column('target_url',
               existing_type=sa.VARCHAR(length=500),
               nullable=True)
        batch_op.alter_column('keyword',
               existing_type=sa.VARCHAR(length=100),
               nullable=True)

    with op.batch_alter_table('outreach_attempt', schema=None) as batch_op:
        # Set a default author_id for existing rows if needed
        batch_op.execute("UPDATE outreach_attempt SET author_id = 1 WHERE author_id IS NULL")
        
        batch_op.alter_column('author_id',
               existing_type=sa.INTEGER(),
               nullable=False)


def downgrade():
    with op.batch_alter_table('outreach_attempt', schema=None) as batch_op:
        batch_op.alter_column('author_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    with op.batch_alter_table('campaign', schema=None) as batch_op:
        batch_op.alter_column('keyword',
               existing_type=sa.VARCHAR(length=100),
               nullable=False)
        batch_op.alter_column('target_url',
               existing_type=sa.VARCHAR(length=500),
               nullable=False)
        batch_op.alter_column('campaign_type',
               existing_type=sa.VARCHAR(length=50),
               nullable=True)
