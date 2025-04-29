# app/routes/admin.py
import os
import tempfile
import pandas as pd
from   app.utils      import *
from   flask          import Blueprint, Response, render_template, redirect, request, url_for, flash
from   flask_babel    import gettext as _
from   app.models     import MeetingCenter
from   flask          import request, flash, redirect, url_for, render_template
from   werkzeug.utils import secure_filename

bp_import = Blueprint('import', __name__)

# =================================================================
@bp_import.route("/members/template")
@role_required('Admin', 'Owner')
def download_template():
    template_data = [
    [_('full_name'), _('gender'), _('marital status'), _('birth_date'), _('address_1'), _('city'), _('state'), _('zip_code'), _('priesthood'), _('priesthood_office'), _('callings'), _('arrival_date'), _('family_head')],
    ["John Doe", "M", "Married","05/20/1990", "123 Main St", "Tooele", "UT", "84223", "Melchisedec", "Elder", "Elders Quorum President", "2024-02-10", "John Doe"],
    ["Gina Doe", "F", "Single","1993-06-18", "123 Main St", "Tooele", "UT", "84223", "", "", "Primary President", "10 Feb 2024", "John Doe"]
]
    df = pd.DataFrame(template_data)
    csv_output = df.to_csv(index=False, header=False)

    return Response(
        csv_output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=members_template.csv"}
    )

# =================================================================
@bp_import.route('/upload', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def upload_file():
    """ Primera vista: carga de archivo y selección de centro de reunión """
    meeting_centers = MeetingCenter.query.all()
    
    if request.method == 'POST':
        file              = request.files.get('file')
        meeting_center_id = request.form.get('meeting_center_id')

        if not file or not allowed_file(file.filename):
            flash(_('You must select a valid file.'), "danger")
            return redirect(url_for('import.upload_file'))
        
        filename  = secure_filename(file.filename)
        temp_dir  = tempfile.gettempdir()  # Obtiene la carpeta temporal del sistema
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)

        # Guardar datos en sesión para la vista de mapeo
        session['uploaded_file']     = file_path
        session['meeting_center_id'] = meeting_center_id

        return redirect(url_for('import.map_columns'))  # Redirigir a la vista de mapeo

    return render_template('imports/upload_file.html', meeting_centers=meeting_centers)


# =================================================================
@bp_import.route('/members', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def import_members():
    """ Tercera vista: Importar miembros según el mapeo definido """
    file_path         = session.get('uploaded_file')
    meeting_center_id = get_meeting_center_id()
    column_mapping    = session.get('column_mapping')

    if not file_path or not meeting_center_id or not column_mapping:
        flash(_('Missing data. Please reload the file.'), "danger")
        return redirect(url_for('import.upload_file'))

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

        flash(_('Import completed. Added: %(added)s, Updated: %(updated)s.') % {'added': added, 'updated': updated}, 'success')

    except Exception as e:
        flash(_('Error during import: %(error)s') %{'error': {str(e)}},'danger')

    return redirect(url_for('import.upload_file'))


# =================================================================
@bp_import.route('/map_columns', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def map_columns():
    file_path = session.get('uploaded_file')
    meeting_center_id = session.get("meeting_center_id")

    if not file_path:
        flash(_('No file uploaded. Please upload a file first.'), "danger")
        return redirect(url_for('import.upload_file'))
    
    if not meeting_center_id:
        flash(_('You need to choose a Meeting Center.'), "danger")
        return redirect(url_for('import.upload_file'))

    column_mapping = session.get('column_mapping', {})

    try:
        ext = file_path.rsplit('.', 1)[-1].lower()
        if ext == 'txt':
            df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
        elif ext == 'csv':
            df = pd.read_csv(file_path, encoding='utf-8')
        else:
            df = pd.read_excel(file_path)

        df.columns   = df.columns.str.strip()
        column_names = df.columns.tolist()
    except Exception as e:
        flash(_('Error reading the file: %(error)s') %{'error': {str(e)}},'danger')
        return redirect(url_for('import.upload_file'))

    required_fields = [
        'full_name', 'gender', 'marital_status', 'birth_date', 'address', 'city', 
        'state', 'arrival_date', 'calling', 'family_head'
    ]
    
    all_fields = [
        'full_name', 'birth_date', 'gender', 'marital_status', 'address',
        'city', 'state', 'zip_code', 'priesthood', 'priesthood_office',
        'arrival_date', 'calling', 'family_head'
    ]
    
    optional_fields             = [field for field in all_fields if field not in required_fields]
    permanently_excluded_fields = ['gender', 'birth_date', 'fixed_address', 'lat', 'lon', 'preferred_name', 'short_name']

    if request.method == 'POST':
        column_mapping            = request.form.to_dict()
        update_fields             = request.form.getlist('update_fields')
        session['column_mapping'] = column_mapping
        session['update_fields']  = update_fields

        flash(_('Column mapping saved successfully.'), "success")
        return redirect(url_for('import.import_members'))

    return render_template(
        'imports/map_columns.html',
        column_names                = column_names,
        required_fields             = required_fields,
        optional_fields             = optional_fields,
        all_fields                  = all_fields,
        column_mapping              = column_mapping,
        permanently_excluded_fields = permanently_excluded_fields
    )