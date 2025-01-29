"""create tables

Revision ID: 1f63e12a063f
Revises: 
Create Date: 2025-01-28 18:10:18.200523

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1f63e12a063f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('meeting_center',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('unit_number', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('short_name', sa.String(length=20), nullable=False),
    sa.Column('city', sa.String(length=50), nullable=True),
    sa.Column('start_time', sa.Time(), nullable=True),
    sa.Column('end_time', sa.Time(), nullable=True),
    sa.Column('is_restricted', sa.Boolean(), nullable=True),
    sa.Column('grace_period_hours', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('unit_number')
    )
    op.create_table('organization',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('setup',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=50), nullable=False),
    sa.Column('value', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('key')
    )
    op.create_table('classes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('class_name', sa.String(length=50), nullable=False),
    sa.Column('short_name', sa.String(length=20), nullable=False),
    sa.Column('class_code', sa.String(length=10), nullable=False),
    sa.Column('class_type', sa.String(length=10), nullable=False),
    sa.Column('schedule', sa.String(length=10), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('class_color', sa.String(length=7), nullable=True),
    sa.Column('meeting_center_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['meeting_center_id'], ['meeting_center.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('class_code', 'meeting_center_id', name='uq_class_code_meeting_center'),
    sa.UniqueConstraint('class_name', 'meeting_center_id', name='uq_class_name_meeting_center'),
    sa.UniqueConstraint('short_name', 'meeting_center_id', name='uq_short_name_meeting_center')
    )
    op.create_table('name_corrections',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('wrong_name', sa.String(length=50), nullable=False),
    sa.Column('correct_name', sa.String(length=50), nullable=False),
    sa.Column('meeting_center_id', sa.Integer(), nullable=False),
    sa.Column('added_by', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['meeting_center_id'], ['meeting_center.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('wrong_name', 'meeting_center_id', name='uq_wrong_name_meeting_center')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('name', sa.String(length=20), nullable=False),
    sa.Column('lastname', sa.String(length=20), nullable=False),
    sa.Column('password_hash', sa.String(length=128), nullable=False),
    sa.Column('role', sa.String(length=10), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('meeting_center_id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['meeting_center_id'], ['meeting_center.id'], ),
    sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('attendance',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('student_name', sa.String(length=50), nullable=False),
    sa.Column('class_id', sa.Integer(), nullable=False),
    sa.Column('class_code', sa.String(length=5), nullable=True),
    sa.Column('sunday_date', sa.Date(), nullable=False),
    sa.Column('sunday_code', sa.String(length=10), nullable=True),
    sa.Column('submit_date', sa.DateTime(), nullable=False),
    sa.Column('meeting_center_id', sa.Integer(), nullable=False),
    sa.Column('fix_name', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ),
    sa.ForeignKeyConstraint(['meeting_center_id'], ['meeting_center.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_name', 'sunday_date', 'meeting_center_id', 'class_id', name='unique_attendance')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('attendance')
    op.drop_table('users')
    op.drop_table('name_corrections')
    op.drop_table('classes')
    op.drop_table('setup')
    op.drop_table('organization')
    op.drop_table('meeting_center')
    # ### end Alembic commands ###
