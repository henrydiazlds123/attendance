"""Agregar restricciones de eliminación a MeetingCenter y Classes

Revision ID: fe69bab084dc
Revises: 7bb2f8f653c2
Create Date: 2025-01-19 06:17:02.007785

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fe69bab084dc'
down_revision = '7bb2f8f653c2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('meeting_center', schema=None) as batch_op:
        batch_op.drop_column('end_time')
        batch_op.drop_column('start_time')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('meeting_center', schema=None) as batch_op:
        batch_op.add_column(sa.Column('start_time', sa.TIME(), nullable=True))
        batch_op.add_column(sa.Column('end_time', sa.TIME(), nullable=True))

    # ### end Alembic commands ###
