"""Modificar Classes

Revision ID: 276d23f4423c
Revises: 8e51dd3f2d82
Create Date: 2025-01-21 20:37:54.660262

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '276d23f4423c'
down_revision = '8e51dd3f2d82'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('classes', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_class_code_meeting_center', ['class_code', 'meeting_center_id'])
        batch_op.create_unique_constraint('uq_class_name_meeting_center', ['class_name', 'meeting_center_id'])
        batch_op.create_unique_constraint('uq_short_name_meeting_center', ['short_name', 'meeting_center_id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('classes', schema=None) as batch_op:
        batch_op.drop_constraint('uq_short_name_meeting_center', type_='unique')
        batch_op.drop_constraint('uq_class_name_meeting_center', type_='unique')
        batch_op.drop_constraint('uq_class_code_meeting_center', type_='unique')

    # ### end Alembic commands ###
