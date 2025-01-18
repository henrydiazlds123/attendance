from flask import Blueprint, abort, jsonify, render_template, redirect, request, session, url_for, flash, send_from_directory
import qrcode
from sqlalchemy import extract, func
from config import BASE_URL, OUTPUT_DIR
from models import Classes, db, User, Attendance, MeetingCenter, Config
from forms import AttendanceEditForm, AttendanceForm, MeetingCenterForm, UserForm, EditUserForm, ResetPasswordForm
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from urllib.parse import unquote
from utils import *


bp = Blueprint('routes', __name__)



@bp.route('/')
def index():
    return render_template('index.html')


# =============================================================================================
#Sesiones
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        meeting_center = MeetingCenter.query.get(user.meeting_center_id)

        if user and user.check_password(password):
            session['user_id']               = user.id
            session['user_name']             = user.name
            session['role']                  = user.role  # Guarda el rol del usuario
            session['meeting_center_id']     = meeting_center.id
            session['meeting_center_name']   = meeting_center.name
            session['meeting_center_number'] = meeting_center.unit_number

            flash('Login successful!', 'success')
            return redirect(url_for('routes.attendances'))
        else:
            flash('Credenciales inválidas.')
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada.')
    return redirect(url_for('routes.index'))


# =============================================================================================
#Error Handlers
@bp.errorhandler(400) 
def not_found(e): 
  return render_template("400.html")

@bp.errorhandler(401) 
def not_found(e): 
  return render_template("401.html")

@bp.errorhandler(403) 
def not_found(e): 
  return render_template("403.html")

@bp.errorhandler(404) 
def not_found(e): 
  return render_template("404.html")


# =============================================================================================
# CRUD para Users
@bp.route('/users')
def users():

    role                = session.get('role')
    meeting_center_id   = session.get('meeting_center_id')
    admin_count         = User.query.filter_by(role='Admin').count()

    if role == 'Owner':
        # Owners can view all attendances across all units
        users = User.query.all()
    elif role == 'Admin':
        # Admins can only view their own meeting center's users
        users = User.query.filter_by(meeting_center_id=meeting_center_id).all()
    else:
        # Regular users can only view their own user
        users = User.query.filter_by(student_name=session.get('username')).all()

    return render_template('users.html', users=users, admin_count=admin_count)

# =============================================================================================
@bp.route('/user/new', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def create_user():
    if not is_admin_or_owner():
        return redirect(url_for('routes.users'))  # Redirect if not authorized
    form = UserForm()
    form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]

    if form.validate_on_submit():
        user = User(
            username         =form.username.data, 
            email            =form.email.data, 
            name             =form.name.data,
            lastname         =form.lastname.data,
            role             =form.role.data,
            meeting_center_id=form.meeting_center_id.data,
            is_active        =form.is_active.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('routes.users'))
    return render_template('form.html', form=form, title="Nuevo Usuario", submit_button_text="Crear", clas="warning")

# =============================================================================================
@bp.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def update_user(id):
    user                              = User.query.get_or_404(id)
    form                              = EditUserForm(obj=user)
    form.meeting_center_id.choices    = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]

    if form.validate_on_submit():
        # form.populate_obj(user)
        user.username             = form.username.data
        user.email                = form.email.data
        user.name                 = form.name.data
        user.lastname             = form.lastname.data
        user.role                 = form.role.data
        user.meeting_center_id    = form.meeting_center_id.data
        user.is_active            = form.is_active.data

        db.session.commit()
        flash('User updated successfully.')
        return redirect(url_for('routes.users'))
    return render_template('form.html', form=form, title="Editar Usuario", submit_button_text="Actualizar", clas="warning")

# =============================================================================================
@bp.route('/user/delete/<int:id>', methods=['POST'])
@role_required('Admin')
def delete_user(id):
    user = User.query.get_or_404(id)
    admin_count = User.query.filter_by(session['role'] == 'Admin').count()
    if session['role'] == 'Admin' and admin_count <= 1:
        flash('No puedes eliminar al último administrador.', 'error')
        return redirect(url_for('list_users'))

    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.')
    return redirect(url_for('routes.users'))

# =============================================================================================
@bp.route('/users/<int:id>/reset_password', methods=['GET', 'POST'])
def reset_password(id):
    user = User.query.get_or_404(id)
    form = ResetPasswordForm()

    if form.validate_on_submit():
        if not user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return render_template('form.html', form=form, title="Reset Password", submit_button_text="Update", clas="danger")

        user.set_password(form.new_password.data)
        db.session.commit()
        flash('Password updated successfully.', 'success')
        return redirect(url_for('routes.users'))

    return render_template('form.html', form=form, title="Change Password", submit_button_text="Update", clas="danger")


# =============================================================================================
@bp.route('/users/<int:id>/promote', methods=['POST'])
@role_required('Owner')
def promote_to_admin(id):
    user = User.query.get_or_404(id)
    if user.role =='Admin':
        flash('El usuario ya es administrador.', 'info')
    else:
        user.role = 'Admin'
        db.session.commit()
        flash(f'El usuario {user.username} ha sido promovido a administrador.', 'success')
    return redirect(url_for('routes.users'))


# =============================================================================================
# CRUD para Attendances
@bp.route('/attendance', methods=['GET', 'POST'])
def attendance():
    class_name = request.args.get('class')
    sunday_code = request.args.get('code')

    # if not class_name or not sunday_code or class_name not in CLASES:
    if not class_name or not sunday_code:
        return render_template('400.html'), 400

    code_verification_setting = Config.query.filter_by(key='code_verification').first()
    code_verification_enabled = code_verification_setting.value if code_verification_setting else 'true'

    if code_verification_enabled == 'false':
        return render_template('attendance.html', class_name=class_name, sunday_code=sunday_code, sunday=get_next_sunday())
    
    expected_code = get_next_sunday_code(get_next_sunday())
    if int(sunday_code) == expected_code:
        return render_template('attendance.html', class_name=class_name, sunday_code=sunday_code, sunday=get_next_sunday())
    else:
        return render_template('403.html'), 403
    


# =============================================================================================
@bp.route('/attendances', methods=['GET', 'POST'])
def attendances():
    # Get user role and meeting_center_id from session
    role = session.get('role')
    meeting_center_id = session.get('meeting_center_id')

    # Get distinct values for filters
    classes  = db.session.query(Classes.id, Classes.short_name).join(Attendance, Attendance.class_id == Classes.id).distinct().all()
    students = db.session.query(Attendance.student_name.distinct()).all()
    sundays  = db.session.query(Attendance.sunday_date.distinct()).all()
    years    = db.session.query(func.strftime('%Y', Attendance.sunday_date).label('year')).distinct().all()
    months   = db.session.query(func.strftime('%m', Attendance.sunday_date).label('month')).distinct().all()
  

    # Get filter parameters from URL query string
    class_name    = request.args.get('class_name')
    student_name  = request.args.get('student_name')
    sunday_date   = request.args.get('sunday_date')

    # Get the configuration for code verification setting
    code_verification_setting = Config.query.filter_by(key='code_verification').first()

    # Build the base query for attendance
    query = db.session.query(
    Attendance.id,
    Attendance.student_name,
    Classes.short_name,
    Attendance.sunday_date,
    Attendance.submit_date,
    Attendance.sunday_code,
    MeetingCenter.name.label('meeting_center_name')
).join(Classes, Attendance.class_id == Classes.id) \
 .join(MeetingCenter, Attendance.meeting_center_id == MeetingCenter.id)

    # Filter based on role and meeting_center_id
    if role == 'Admin':
        query = query.filter(Attendance.meeting_center_id == meeting_center_id)
    elif role == 'Owner':
        pass

    # Apply filters based on form inputs
    if class_name:
        query = query.filter(Classes.short_name.ilike(f'%{class_name}%'))
    if student_name:
        query = query.filter(Attendance.student_name.ilike(f'%{student_name}%'))
    if sunday_date:
        try:
            date_filter = datetime.strptime(sunday_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.sunday_date == date_filter)
        except ValueError:
            pass

    selected_year = request.args.get('year')
    if selected_year:
        query = query.filter(func.strftime('%Y', Attendance.sunday_date) == selected_year)

    selected_month = request.args.get('month')
    if selected_month:
        query = query.filter(func.strftime('%m', Attendance.sunday_date) == selected_month.zfill(2))

    # Execute the query and fetch results
    attendances     = query.order_by(Attendance.student_name, Attendance.sunday_date, Attendance.class_id).all()
    total_registros = len(attendances)
    has_records     = Attendance.query.count() > 0

    # Handle POST requests for code verification and deleting records
    if request.method == 'POST':
        if 'code_verification' in request.form:
            new_value = request.form.get('code_verification')
            if code_verification_setting:
                code_verification_setting.value = new_value
            else:
                code_verification_setting = Config(key='code_verification', value=new_value)
                db.session.add(code_verification_setting)
            db.session.commit()

        if 'delete_selected' in request.form:
            ids_to_delete = request.form.getlist('delete')
            for id in ids_to_delete:
                attendance = Attendance.query.get(id)
                if attendance:
                    db.session.delete(attendance)
            db.session.commit()

        elif 'delete_all' in request.form:
            db.session.query(Attendance).delete()
            db.session.commit()

        return redirect(url_for('routes.attendances'))

    verification_enabled = code_verification_setting.value if code_verification_setting else 'true'
    
    return render_template('attendances.html', attendances=attendances, verification_enabled=verification_enabled,
                           has_records=has_records, classes=classes, students=students, sundays=sundays, months=months,
                           years=years, total_registros=total_registros)


# =============================================================================================
@bp.route('/attendance/new', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def create_attendance():
    form = AttendanceForm()
    form.class_id.choices          = [(c.id, c.class_name) for c in Classes.query.all()]
    form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]

    if request.method == 'GET':
        form.set_default_sunday_date() 

    # Populate student name choices dynamically with current student names
    existing_students          = db.session.query(Attendance.student_name).distinct().all()
    form.student_name.choices += [(name[0], name[0]) for name in existing_students]
    

    if form.validate_on_submit():
        # Determine whether to use an existing student name or a new one
        student_name = form.new_student_name.data.strip() if form.new_student_name.data else form.student_name.data

        # Check if no name was provided in either field
        if not student_name:
            flash('Please select an existing student or provide a new name.', 'danger')
            return render_template('form.html', form=form, title="Crear Asistencia Manual", submit_button_text="Crear", clas="warning")

        # Calculate sunday_code based on the provided sunday date
        # sunday_code = get_next_sunday_code(form.sunday_date.data)
        sunday_code = '0000'

        attendance = Attendance(
            student_name     = student_name,
            class_id         = form.class_id.data,
            sunday_date      = form.sunday_date.data,
            sunday_code      = sunday_code,
            meeting_center_id= form.meeting_center_id.data
        )
        db.session.add(attendance)
        db.session.commit()
        flash('Attendance registered successfully!')
        return redirect(url_for('routes.attendances'))

    return render_template('form.html', form=form, title="Crear Asistencia Manual", submit_button_text="Crear", clas="warning")


# =============================================================================================
@bp.route('/attendance/edit/<int:id>', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def update_attendance(id):
    attendance                     = Attendance.query.get_or_404(id)
    form                           = AttendanceEditForm(obj=attendance)
    form.class_id.choices          = [(c.id, c.short_name) for c in Classes.query.all()]
    # form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]

    if form.validate_on_submit():
        attendance.student_name      =form.student_name.data
        attendance.class_id          =form.class_id.data 
        attendance.sunday_date       =form.sunday_date.data
        # attendance.submit_date       =form.submit_date.data
        # attendance.meeting_center_id =form.meeting_center_id.data

        db.session.commit()
        flash('Attendance record updated successfully.')
        return redirect(url_for('routes.attendances'))
    return render_template('form.html', form=form, title="Editar Asistencia", submit_button_text="Actualizar", clas="warning")


# =============================================================================================
@bp.route('/attendance/delete/<int:id>', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def delete_attendance(id):
    if not is_admin_or_owner():
        return redirect(url_for('routes.attendances'))  # Redirect if not authorized
    
    attendance = Attendance.query.get_or_404(id)
    db.session.delete(attendance)
    db.session.commit()
    flash('Attendance record deleted successfully.')
    return redirect(url_for('routes.attendances'))


# =============================================================================================
@bp.route('/registrar', methods=['POST'])
def registrar():
    try:
        student_name        = request.form.get('studentName').title()
        nombre, apellido    = student_name.split(" ", 1)
        formatted_name      = f"{apellido}, {nombre}"
        class_code          = request.form.get('className')  # Usar código de clase en lugar del nombre
        sunday_date         = get_next_sunday()
        sunday_code         = request.form.get('sunday_code')
        unit_number         = request.form.get('unitNumber')

        # Verificar si la clase es válida
        class_entry = Classes.query.filter_by(class_code=class_code).first()
        if not class_entry:
            return jsonify({
                "success": False,
                "message": "La clase seleccionada no es válida.",
            }), 400

        # Verificar si el MeetingCenter es válido
        meeting_center = MeetingCenter.query.filter_by(unit_number=unit_number).first()
        if not meeting_center:
            return jsonify({
                "success": False,
                "message": "El centro de reuniones no es válido.",
            }), 400

        # Verificar si ya existe un registro para este estudiante, clase, y fecha
        existing_attendance   = Attendance.query.filter_by(
            student_name      = formatted_name,
            class_id          = class_entry.id,
            sunday_date       = sunday_date,
            meeting_center_id = meeting_center.id
        ).first()

        if existing_attendance:
            return jsonify({
                "success": False,
                "message": "El estudiante ya tiene un registro para esta clase y fecha.",
                "nombre": nombre,
                "sunday_date": sunday_date.strftime("%b %d, %Y")
            }), 400

        # Registrar la asistencia
        new_attendance          = Attendance(
            student_name        = formatted_name,
            class_id            = class_entry.id,
            sunday_date         = sunday_date,
            sunday_code         = sunday_code,
            meeting_center_id   = meeting_center.id
        )
        db.session.add(new_attendance)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Asistencia registrada exitosamente.",
            "student_name": student_name,
            "class_name": class_entry.class_name,
            "sunday_date": sunday_date.strftime("%b %d, %Y")
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Hubo un error al registrar la asistencia: {str(e)}"
        }), 500




# =============================================================================================
@bp.route('/manual_attendance')
def manual_attendance():
    """Genera enlaces solo para las clases correspondientes al próximo domingo."""

    next_sunday_code = get_next_sunday_code(get_next_sunday())
    sunday_week      = (get_next_sunday().day - 1) // 7 + 1  # Determina la semana del mes
    unit             = session['meeting_center_number']
    
        
    # Generar enlaces solo para las clases correspondientes

    class_links = {
    class_entry.class_code: f"{BASE_URL}/attendance?class_name={class_entry.class_name}&class={class_entry.class_code}&code={next_sunday_code}&unit={unit}"
    for class_entry in Classes.query.all() if str(sunday_week) in class_entry.schedule.split(',')
}

    return render_template('manual_attendance.html', class_links=class_links)


# =============================================================================================
# Rutas para la Administracion de PDF
@bp.route('/list_pdfs', methods=['GET'])
def list_pdfs():
    directory = os.path.join(os.getcwd(), OUTPUT_DIR)
    pdf_files = os.listdir(directory)
    return render_template('list_pdfs.html', pdf_files=pdf_files)

# =============================================================================================
# Botones en la interfaz para generar PDFs:
@bp.route('/generate_all_pdfs', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def generate_all_pdfs():
    return redirect(url_for('routes.generate_pdfs', type='todos'))  # redirige a la misma función con parámetro "todos"

# =============================================================================================
@bp.route('/generate_week_pdfs', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def generate_week_pdfs():
    return redirect(url_for('routes.generate_pdfs', type='semana_especifica'))  # redirige a la misma función para PDFs de la semana específica

# =============================================================================================
@bp.route('/generate_pdfs', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def generate_pdfs():
    """Genera PDFs con códigos QR para las clases correspondientes a un domingo específico."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    sunday_week = get_sunday_week(get_next_sunday())  # 1 para el primer domingo, 2 para el segundo, etc.

    # Verificar si el usuario quiere todos los PDFs o solo los de la semana específica
    if request.args.get('type') == 'todos':
        clases_a_imprimir = [c.class_name for c in Classes.query.all()]
    else:
        clases_a_imprimir = [c.class_name for c in Classes.query.all() if str(sunday_week) in c.schedule.split(',')]

    next_sunday_code = get_next_sunday_code(get_next_sunday())
    clean_qr_folder(OUTPUT_DIR)
   
    for class_name in clases_a_imprimir:
   
        qr_url = f"{BASE_URL}/attendance?class={class_name.replace(' ', '+')}&code={next_sunday_code}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        qr_filename = os.path.join(OUTPUT_DIR, f"{class_name}_{get_next_sunday()}.png")
        img.save(qr_filename)
        
        pdf_filename = os.path.join(OUTPUT_DIR, f"{class_name}_{get_next_sunday()}.pdf")
        c = canvas.Canvas(pdf_filename, pagesize=letter)
        page_width, page_height = letter
        
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(page_width / 2, 670, f"Lista de Asistencia")
        c.setFont("Helvetica-Bold", 35)
        c.drawCentredString(page_width / 2, 625, class_name)
        
        qr_image = ImageReader(qr_filename)
        qr_size = 450
        qr_x = (page_width - qr_size) / 2
        qr_y = (page_height - qr_size) / 2
        c.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)
        
        c.setFont("Helvetica", 18)
        c.drawCentredString(page_width / 2, qr_y - 15, f"Fecha: {get_next_sunday()}")
        c.save()

    clean_qr_images(OUTPUT_DIR)
    return redirect(url_for('routes.list_pdfs'))


# =============================================================================================
@bp.route('/download_pdf/<path:filename>', methods=['GET'])
def download_pdf(filename):
    try:
        directory = os.path.join(os.getcwd(), OUTPUT_DIR)
        filename = unquote(filename)
        full_path = os.path.join(directory, filename)

        print(f"Trying to download from: {full_path}")  # Debugging output

        if not os.path.exists(full_path):
            print("File not found:", full_path)  # More detailed log
            abort(404, description=f"File not found: {filename}")

        return send_from_directory(directory, filename, as_attachment=True)
    except Exception as e:
        print(f"Error: {e}")  # Log the actual error for debugging
        abort(500, description=str(e))

# =============================================================================================
# CRUD para Meeting Centers
@bp.route('/meeting_centers/', methods=['GET', 'POST'])
@role_required('Owner')
def meeting_centers():
    meeting_centers = MeetingCenter.query.all()
    return render_template('meeting_centers.html', meeting_centers=meeting_centers)
    
@bp.route('/meeting_center/new', methods=['GET', 'POST'])
@role_required('Owner')
def create_meeting_center():
    form = MeetingCenterForm()
    if form.validate_on_submit():
        meeting_center = MeetingCenter(
            unit_number=form.unit_number.data,
            name       =form.name.data,
            city       =form.city.data
        )
        db.session.add(meeting_center)
        db.session.commit()
        flash('Meeting center created successfully!', 'success')
        return redirect(url_for('routes.meeting_centers'))
    return render_template('form.html', form=form, title="Crear Centro de Reunión", submit_button_text="Crear", clas="warning")


# =============================================================================================
@bp.route('/meeting_center/edit/<int:id>', methods=['GET', 'POST'])
@role_required('Owner')
def update_meeting_center(id):
    meeting_center = MeetingCenter.query.get_or_404(id)
    form = MeetingCenterForm(obj=meeting_center)
    if form.validate_on_submit():
        form.populate_obj(meeting_center)
        db.session.commit()
        flash('Meeting Center updated successfully.')
        return redirect(url_for('routes.meeting_centers'))
    return render_template('form.html', form=form, title="Editar Centro de Reunión", submit_button_text="Actualizar", clas="warning")


# =============================================================================================
@bp.route('/meeting_center/delete/<int:id>', methods=['POST'])
@role_required('Owner')
def delete_meeting_center(id):
    meeting_center = MeetingCenter.query.get_or_404(id)
    db.session.delete(meeting_center)
    db.session.commit()
    flash('Meeting Center deleted successfully.')
    return redirect(url_for('routes.meeting_centers'))
