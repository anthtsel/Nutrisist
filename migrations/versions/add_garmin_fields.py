"""add garmin fields

Revision ID: add_garmin_fields
Revises: add_device_model
Create Date: 2024-03-21 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_garmin_fields'
down_revision = 'add_device_model'
branch_labels = None
depends_on = None

def upgrade():
    # Add Garmin OAuth fields to users table
    op.add_column('users', sa.Column('garmin_access_token', sa.String(256), nullable=True))
    op.add_column('users', sa.Column('garmin_refresh_token', sa.String(256), nullable=True))
    op.add_column('users', sa.Column('garmin_token_expires_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('garmin_connected', sa.Boolean(), nullable=True, server_default='false'))

def downgrade():
    # Remove Garmin OAuth fields from users table
    op.drop_column('users', 'garmin_connected')
    op.drop_column('users', 'garmin_token_expires_at')
    op.drop_column('users', 'garmin_refresh_token')
    op.drop_column('users', 'garmin_access_token') 