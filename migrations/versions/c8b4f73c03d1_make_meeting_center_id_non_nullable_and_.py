from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8b4f73c03d1'
down_revision = '1f63e12a063f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('setup', schema=None) as batch_op:
        # Agregar la columna meeting_center_id
        batch_op.add_column(sa.Column('meeting_center_id', sa.Integer(), nullable=True))

    # Actualizar las filas existentes para darles un valor predeterminado (1) para meeting_center_id
    op.execute('UPDATE setup SET meeting_center_id = 1 WHERE meeting_center_id IS NULL')

    # Ahora establecer la columna como no nula
    with op.batch_alter_table('setup', schema=None) as batch_op:
        batch_op.alter_column('meeting_center_id', nullable=False)

    # Crear restricciones y relaciones con nombres específicos
    with op.batch_alter_table('setup', schema=None) as batch_op:
        # Constraint de unicidad
        batch_op.create_unique_constraint('uq_key_meeting_center', ['key', 'meeting_center_id'])
        # Índice para la columna meeting_center_id
        batch_op.create_index(batch_op.f('ix_setup_meeting_center_id'), ['meeting_center_id'], unique=False)
        # Clave foránea
        batch_op.create_foreign_key('fk_meeting_center_id', 'meeting_center', ['meeting_center_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('setup', schema=None) as batch_op:
        # Eliminar las restricciones y relaciones
        batch_op.drop_constraint('fk_meeting_center_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_setup_meeting_center_id'))
        batch_op.drop_constraint('uq_key_meeting_center', type_='unique')
        batch_op.drop_column('meeting_center_id')

    # ### end Alembic commands ###
