from flask                   import Blueprint, jsonify, render_template, redirect, request, session, url_for, flash
from flask_babel             import gettext as _
from models                  import db, Attendance, MeetingCenter, Setup, NameCorrections
from utils                   import *

bp_correction = Blueprint('correction', __name__)

# =============================================================================================
@bp_correction.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_name_correction(id):
    correction = NameCorrections.query.get_or_404(id)  # Buscar el registro por ID
    db.session.delete(correction)  # Eliminar el registro
    db.session.commit()  # Guardar los cambios
    flash(_('Name correction deleted successfully!'), "success")
    return redirect(url_for('admin.admin'))  # Redirigir a la vista admin


# =============================================================================================
@bp_correction.route('/revert/<int:id>', methods=['POST'])
@login_required
def revert_name_correction(id):
    # Obtener la corrección de nombre
    correction = NameCorrections.query.get_or_404(id)
    meeting_center_id = correction.meeting_center_id

    # Buscar en la tabla Attendance los registros que coincidan con correct_name y meeting_center_id
    attendances = Attendance.query.filter(
        Attendance.student_name == correction.correct_name,
        Attendance.meeting_center_id == meeting_center_id
    ).all()

    # Revertir los nombres en la tabla Attendance
    for attendance in attendances:
        attendance.student_name = correction.wrong_name
        attendance.fix_name = False  # Desmarcar la corrección

    # Eliminar la entrada de NameCorrections
    db.session.delete(correction)

    # Guardar los cambios en la base de datos
    db.session.commit()

    flash(_('Name correction reverted successfully!'), "success")
    return redirect(url_for('admin.admin'))


# =============================================================================================
@bp_correction.route('/filter', methods=['GET'])
@login_required
def filter_name_corrections():
    meeting_center_id = request.args.get('meeting_center_id', type=int)
    
    if meeting_center_id == 'all' or meeting_center_id is None:
        name_corrections = NameCorrections.query.all()
    else:
        name_corrections = NameCorrections.query.filter_by(meeting_center_id=meeting_center_id).all()
    
    return render_template('partials/tables/name_correction_table.html', name_corrections=name_corrections)


# =============================================================================================
@bp_correction.route('/update', methods=['POST'])
@role_required('Admin', 'Super', 'Owner')
def update_name_correction():
    data = request.get_json()
    # print("Datos recibidos:", data)  # Esto imprimirá los datos recibidos para depurar
    
    wrong_name        = data.get('wrong_name')
    correct_name      = data.get('correct_name')
    meeting_center_id = data.get('meeting_center_id')
    admin_name        = session.get('user_name')

    if not wrong_name or not correct_name or not meeting_center_id:
        return jsonify({'error': _('Missing required fields')}), 400

    # Verifica si ya existe un registro con ese nombre incorrecto para el meeting center
    correction = NameCorrections.query.filter_by(wrong_name=wrong_name, meeting_center_id=meeting_center_id).first()
    if correction:
        correction.correct_name = correct_name
    else:
        correction = NameCorrections(
            wrong_name        = wrong_name,
            correct_name      = correct_name,
            meeting_center_id = meeting_center_id,
            added_by          = admin_name
        )
        db.session.add(correction)

    # Actualiza los registros en Attendance
    attendances_to_update = Attendance.query.filter_by(student_name=wrong_name, meeting_center_id=meeting_center_id).all()
    for attendance in attendances_to_update:
        attendance.student_name = correct_name
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        # print(f"Error al guardar en la base de datos: {e}")
        return jsonify({'error': 'Error al guardar la corrección'}), 500


