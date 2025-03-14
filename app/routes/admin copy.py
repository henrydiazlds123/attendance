# app/routes/admin.py
import os
import tempfile
import pandas as pd

from app.utils   import *
from flask       import Blueprint, Response, jsonify, logging, render_template, redirect, request, url_for, flash
from flask_babel import gettext as _
from app.models  import db, Attendance, MeetingCenter, Setup, NameCorrections, Member
from flask       import current_app, request, flash, redirect, url_for, render_template
from werkzeug.utils import secure_filename

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

# =================================================================
@bp_admin.route("/import/members/template")
def download_template():
    #Nombre de preferencia,Sexo,Fecha de nacimiento,Dirección - Calle 1,Dirección - Calle 2,Dirección - Ciudad,Dirección - Estado o Provincia,Dirección - código postal,Sacerdocio,Oficio en el sacerdocio,Llamamientos,Fecha de llegada a la unidad,El cabeza de familia
    template_data = [
    [_('full_name'), _('gender'), _('birth_date'), _('address_1'), _('city'), _('state'), _('zip_code'), _('priesthood'), _('priesthood_office'), _('callings'), _('arrival_date'), _('family_head')],
    ["John Doe", "M", "1990-05-20", "123 Main St", "Tooele", "UT", "84223", "Melchisedec", "Elder", "Elders Quorum President", "2024-02-10", "John Doe"],
    ["Gina Doe", "F", "1993-06-18", "123 Main St", "Tooele", "UT", "84223", "", "", "Primary President", "2024-02-10", "John Doe"]
]
    df = pd.DataFrame(template_data)
    csv_output = df.to_csv(index=False, header=False)

    return Response(
        csv_output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=members_template.csv"}
    )

# =================================================================
@bp_admin.route('/import/upload', methods=['GET', 'POST'])
def upload_file():
    """ Primera vista: carga de archivo y selección de centro de reunión """
    meeting_centers = MeetingCenter.query.all()
    
    if request.method == 'POST':
        file = request.files.get('file')
        meeting_center_id = request.form.get('meeting_center_id')

        if not file or not allowed_file(file.filename):
            flash("Debe seleccionar un archivo válido.", "danger")
            return redirect(url_for('admin.upload_file'))
        
        filename = secure_filename(file.filename)
        temp_dir = tempfile.gettempdir()  # Obtiene la carpeta temporal del sistema
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)

        # Guardar datos en sesión para la vista de mapeo
        session['uploaded_file'] = file_path
        session['meeting_center_id'] = meeting_center_id

        return redirect(url_for('admin.map_columns'))  # Redirigir a la vista de mapeo

    return render_template('imports/upload_file.html', meeting_centers=meeting_centers)


# =================================================================
@bp_admin.route('/import/members', methods=['GET', 'POST'])
def import_members():
    """ Tercera vista: Importar miembros según el mapeo definido """
    file_path         = session.get('uploaded_file')
    meeting_center_id = get_meeting_center_id()
    column_mapping    = session.get('column_mapping')


    if not file_path or not meeting_center_id or not column_mapping:
        flash("Faltan datos. Vuelva a cargar el archivo.", "danger")
        return redirect(url_for('admin.upload_file'))

    try:
        ext = file_path.rsplit('.', 1)[-1].lower()
        if ext == 'txt':
            df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
        elif ext == 'csv':
            df = pd.read_csv(file_path, encoding='utf-8')
        else:
            df = pd.read_excel(file_path)

        # 🔹 Limpiar nombres de columnas eliminando espacios extra
        df.columns = df.columns.str.strip()

        # 🔹 Aplicar el mapeo solo a las columnas que existen en el CSV
        df_mapped = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

        # 🔹 Llamar a la función que procesa la importación
        added, updated = process_import(df_mapped, column_mapping, meeting_center_id)

        flash(f"Importación completada. Agregados: {added}, Actualizados: {updated}.", "success")

    except Exception as e:
        flash(f"Error durante la importación: {str(e)}", "danger")

    return redirect(url_for('admin.upload_file'))


# =================================================================
@bp_admin.route('/import/map', methods=['GET', 'POST'])
def map_columns():
    file_path = session.get('uploaded_file')
    meeting_center_id = session.get("meeting_center_id")

    if not file_path:
        flash("No hay un archivo cargado. Por favor, suba un archivo primero.", "danger")
        return redirect(url_for('admin.upload_file'))
    
    if not meeting_center_id:
        flash("Necesita escoger un Centro de reuniones.", "danger")
        return redirect(url_for('admin.upload_file'))

    # Inicializar column_mapping para evitar el error
    column_mapping = session.get('column_mapping', {})

    try:
        # Determinar el tipo de archivo y leerlo
        ext = file_path.rsplit('.', 1)[-1].lower()
        if ext == 'txt':
            df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
        elif ext == 'csv':
            df = pd.read_csv(file_path, encoding='utf-8')
        else:
            df = pd.read_excel(file_path)

        # Limpiar los nombres de las columnas eliminando espacios extra
        df.columns = df.columns.str.strip()
        
        # Lista de columnas requeridas y opcionales
        column_names = df.columns.tolist()
    except Exception as e:
        flash(f"Error al leer el archivo: {str(e)}", "danger")
        return redirect(url_for('admin.upload_file'))

    required_fields = [
        'full_name', 'gender', 'birth_date', 'address', 'city', 
        'state', 'arrival_date', 'calling', 'family_head',
    ]
    
    all_fields = [
        'full_name', 'birth_date', 'gender', 'address',
        'city', 'state', 'zip_code', 'priesthood', 'priesthood_office',
        'arrival_date', 'family_head'
    ]
    
    optional_fields = [field for field in all_fields if field not in required_fields]

    if request.method == 'POST':
        # Guardar el nuevo mapeo desde el formulario
        column_mapping = request.form.to_dict()
        session['column_mapping'] = column_mapping  # Guardar en sesión

        # Filtrar las columnas mapeadas (de acuerdo a las columnas necesarias)
        df_mapped = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

        df_mapped = df_mapped[[col for col in all_fields if col in df_mapped.columns]]


        flash("Mapeo de columnas guardado correctamente.", "success")
        return redirect(url_for('admin.import_members'))

    return render_template(
        'imports/map_columns.html',
        column_names=column_names,
        required_fields=required_fields,
        optional_fields=optional_fields,
        column_mapping=column_mapping  # Pasar mapeo a la plantilla
    )
