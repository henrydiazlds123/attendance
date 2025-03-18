# app/routes/admin.py
from app.utils   import *
from flask       import Blueprint, jsonify, render_template, redirect, request, url_for, flash
from flask_babel import gettext as _
from app.models  import db, Attendance, MeetingCenter, Setup, NameCorrections
from flask       import request, flash, redirect, url_for, render_template

bp_admin = Blueprint('admin', __name__)

# =============================================================================================       
@bp_admin.route('/', methods=['GET', 'POST'])
@role_required('Admin', 'Super', 'Owner')
def admin():
    meeting_center_id = get_meeting_center_id()
    
    name_corrections_query = NameCorrections.query
    if meeting_center_id != 'all':
        name_corrections_query = name_corrections_query.filter_by(meeting_center_id=meeting_center_id)

    name_corrections = name_corrections_query.order_by(None).order_by(NameCorrections.wrong_name.asc()).all()

    code_verification_setting = Setup.query.filter_by(
        key='code_verification', meeting_center_id=meeting_center_id if meeting_center_id != 'all' else None
    ).first()

    bypass_enabled = request.args.get('bypass_enabled', 'false')

    if request.method == 'POST':
        if 'code_verification' in request.form:
            new_value = request.form.get('code_verification')
            if code_verification_setting:
                code_verification_setting.value = new_value
            else:
                db.session.add(Setup(key='code_verification', value=new_value, meeting_center_id=meeting_center_id))
            db.session.commit()

        if 'delete_selected' in request.form:
            ids_to_delete = request.form.getlist('delete')
            Attendance.query.filter(Attendance.id.in_(ids_to_delete)).delete(synchronize_session=False)
            db.session.commit()

        elif 'delete_all' in request.form:
            db.session.query(Attendance).delete()
            db.session.commit()

        return redirect(url_for('admin.admin', meeting_center_id=meeting_center_id))
    
    verification_enabled = code_verification_setting.value if code_verification_setting else 'true'

    return render_template('admin/admin.html', 
                           verification_enabled = verification_enabled,
                           bypass_enabled       = bypass_enabled,
                           name_corrections     = name_corrections,
                           meeting_center_id    = meeting_center_id)


# ============================================================================================= 
@bp_admin.route('/get_settings', methods=['GET'])
@login_required
def get_settings():
    meeting_center_id = request.args.get('meeting_center_id')
    
    # Obtener los valores de code_verification y bypass_restriction
    code_verification_setting  = Setup.query.filter_by(key='code_verification', meeting_center_id=meeting_center_id).first()
    bypass_restriction_setting = Setup.query.filter_by(key='bypass_restriction', meeting_center_id=meeting_center_id).first()
    
    # Devolver los valores en formato JSON
    return jsonify({
        'code_verification': code_verification_setting.value if code_verification_setting else 'null',
        'bypass_restriction': bypass_restriction_setting.value if bypass_restriction_setting else 'null'
    })
# =============================================================================================  
@bp_admin.route('/bypass', methods=['POST'])
@login_required
def update_bypass_restriction():
    new_value = request.form.get('bypass_restriction', 'false')  # Default "false"
    meeting_center_id = get_meeting_center_id()  # Obtener el ID del centro de reunión actual

    # Buscar el registro en la base de datos para el centro de reunión y la clave
    bypass_entry = Setup.query.filter_by(key='bypass_restriction', meeting_center_id=meeting_center_id).first()

    if bypass_entry:
        # Si ya existe, actualiza el valor
        bypass_entry.value = new_value
    else:
        # Si no existe, crea un nuevo registro
        bypass_entry = Setup(key='bypass_restriction', value=new_value, meeting_center_id=meeting_center_id)
        db.session.add(bypass_entry)

    db.session.commit()  # Guarda los cambios

    flash(_('Bypass restriction updated successfully!'), "success")
    return redirect(url_for('admin.admin', bypass_enabled=new_value))


# =============================================================================================
@bp_admin.route('/api/data')
@login_required
def admin_data():
    meeting_center_id = request.args.get('meeting_center_id')

    meeting_center = None
    if meeting_center_id and meeting_center_id != 'all':
        meeting_center = MeetingCenter.query.filter_by(id=meeting_center_id).first()

    # Si no se encuentra el meeting center, devuelve uno por defecto
    if not meeting_center:
        meeting_center = {
            "name": _('All Meeting Centers'),
            "unit_number": _('All')
        }
    else:
        # Convertir el objeto MeetingCenter a un diccionario
        meeting_center = {
            "name": meeting_center.name,
            "unit_number": meeting_center.unit_number
        }
    # Devolver los datos del meeting center como JSON
    return jsonify(meeting_center)


