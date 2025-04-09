"""add device model

Revision ID: add_device_model
Revises: cc5bf198407c
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_device_model'
down_revision = 'cc5bf198407c'
branch_labels = None
depends_on = None

def upgrade():
    # Create devices table
    op.create_table('devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('device_name', sa.String(100), nullable=True),
        sa.Column('device_id', sa.String(100), nullable=True),
        sa.Column('last_sync', sa.DateTime(), nullable=True),
        sa.Column('sync_frequency', sa.Integer(), nullable=True, server_default='6'),
        sa.Column('auto_sync', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'platform', name='user_platform_unique_constraint')
    )

def downgrade():
    # Drop devices table
    op.drop_table('devices') 