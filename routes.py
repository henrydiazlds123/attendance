from flask import Blueprint, abort, jsonify, render_template, redirect, request, session, url_for, flash, send_from_directory, send_file
import qrcode
from sqlalchemy import func
from config import Config
from models import db, Classes, User, Attendance, MeetingCenter, Setup, Organization
from forms import AttendanceEditForm, AttendanceForm, MeetingCenterForm, UserForm, EditUserForm, ResetPasswordForm, ClassForm, OrganizationForm
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from urllib.parse import unquote
from utils import *
from sqlalchemy.exc import IntegrityError


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

        if user and user.check_password(password):  # Verifica si el usuario y la contraseña son correctos
            meeting_center                   = MeetingCenter.query.get(user.meeting_center_id)
            session['user_id']               = user.id
            session['user_name']             = user.name
            session['role']                  = user.role  # Guarda el rol del usuario
            session['meeting_center_id']     = meeting_center.id
            session['meeting_center_name']   = meeting_center.name
            session['meeting_center_number'] = meeting_center.unit_number

            flash('Login successful!', 'success')
            return redirect(url_for('routes.attendances'))
        else:
            flash('Invalid credentials. Please check your username and password..', 'danger')
    return render_template('login.html')

# =============================================================================================
@bp.route('/logout')
def logout():
    session.clear()
    flash('Logout successful!', 'success')
    return redirect(url_for('routes.login'))


# =============================================================================================
@bp.route('/reset_name')
def reset_name():
    """Renderiza una página para mostrar el nombre almacenado y borrarlo con confirmación."""
    return render_template('reset_name.html')

# =============================================================================================

# @bp.route('/users')
# @role_required('Admin', 'Owner')
# def users():
#     role                = session.get('role')
#     meeting_center_id   = session.get('meeting_center_id')
#     admin_count         = User.query.filter_by(role='Admin').count()

#     if role == 'Owner':
#         # Los Owners pueden ver todos los usuarios
#         query = db.session.query(
#             User.id,
#             User.username,
#             User.email,
#             User.role,
#             MeetingCenter.short_name.label('meeting_short_name'),
#             Organization.name.label('organization_name')
#             ).join(MeetingCenter, User.meeting_center_id == MeetingCenter.id).join(Organization, User.organization_id == Organization.id)
            

                                
#         users = query.all()
#     elif role == 'Admin':
#         # Los Admins solo pueden ver los usuarios de su Meeting Center, excluyendo a los Owners
#         users = User.query.filter_by(meeting_center_id=meeting_center_id).filter(User.role != 'Owner').all()
#     else:
#         # Los usuarios regulares solo pueden ver su propio usuario
#         users = User.query.filter_by(student_name=session.get('username')).all()

#     return render_template('users.html', users=users, admin_count=admin_count)

@bp.route('/users')
@role_required('Admin', 'Owner')
def users():
    role = session.get('role')
    meeting_center_id = session.get('meeting_center_id')
    admin_count = User.query.filter_by(role='Admin').count()

    if role == 'Owner':
        # Los Owners pueden ver todos los usuarios
        query = db.session.query(
            User.id,
            User.username,
            User.email,
            User.role,
            MeetingCenter.short_name.label('meeting_short_name'),
            Organization.name.label('organization_name')
        ).join(MeetingCenter, User.meeting_center_id == MeetingCenter.id).join(Organization, User.organization_id == Organization.id)

        users = query.all()
    elif role == 'Admin':
        # Los Admins solo pueden ver los usuarios de su Meeting Center, excluyendo a los Owners
        users = db.session.query(
           User.id,
            User.username,
            User.email,
            User.role,
            Organization.name.label('organization_name')
        ).join(MeetingCenter, User.meeting_center_id == MeetingCenter.id).join(Organization, User.organization_id == Organization.id).filter(User.role != 'Owner').all()
    else:
        # Los usuarios regulares solo pueden ver su propio usuario
        users = User.query.filter_by(student_name=session.get('username')).all()

    return render_template('users.html', users=users, admin_count=admin_count)





# =============================================================================================
@bp.route('/user/new', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def create_user():

    form                           = UserForm()
    form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]
    form.organization_id.choices   = [(og.id, og.name) for og in Organization.query.all()]

    if form.validate_on_submit():
        user = User(
            username         =form.username.data, 
            email            =form.email.data, 
            name             =form.name.data,
            lastname         =form.lastname.data,
            role             =form.role.data,
            meeting_center_id=form.meeting_center_id.data,
            organization_id  =form.organization_id.data,
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
    user                           = User.query.get_or_404(id)
    form                           = EditUserForm(obj=user)
    form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]
    form.organization_id.choices   = [(og.id, og.name) for og in Organization.query.all()]

    if form.validate_on_submit():
        user.username          = form.username.data
        user.email             = form.email.data
        user.name              = form.name.data
        user.lastname          = form.lastname.data
        user.role              = form.role.data
        user.meeting_center_id = form.meeting_center_id.data
        user.is_active         = form.is_active.data

        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('routes.users'))
    return render_template('form.html', form=form, title="Editar Usuario", submit_button_text="Actualizar", clas="warning")

@bp.route('/user/delete/<int:id>', methods=['POST'])
@role_required('Admin', 'Owner')  # Solo los admins pueden acceder a esta ruta
def delete_user(id):
    user_to_delete = User.query.get_or_404(id)
    current_user_id = session.get('user_id')
    current_user_role = session.get('role')

    # Contar cuántos admins existen en total
    admin_count = User.query.filter_by(role='Admin').count()

    # Verificar si el usuario actual es Owner
    if current_user_role == 'Owner':
        if user_to_delete.role == 'Admin' and admin_count <= 1:
            flash('No puedes eliminar al último administrador.', 'danger')
            return redirect(url_for('routes.users'))
        
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('Usuario eliminado exitosamente.', 'success')
        return redirect(url_for('routes.users'))

    # Los Admin no pueden eliminar a otros Admin
    if user_to_delete.role == 'Admin':
        flash('No puedes eliminar a otro administrador.', 'danger')
        return redirect(url_for('routes.users'))

    # Los Admin pueden eliminar a un usuario común (User)
    if current_user_id == user_to_delete.id:  # Permitir que un admin se elimine a sí mismo
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('Te has eliminado a ti mismo exitosamente.', 'success')
        return redirect(url_for('auth.login'))  # Redirigir a la página de login

    db.session.delete(user_to_delete)
    db.session.commit()
    flash('Usuario eliminado exitosamente.', 'success')
    return redirect(url_for('routes.users'))

# =============================================================================================
@bp.route('/users/<int:id>/reset_password', methods=['GET', 'POST'])
def reset_password(id):
    user = User.query.get_or_404(id)
    form = ResetPasswordForm()

    if form.validate_on_submit():
        if not user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
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
    class_code  = request.args.get('class')
    sunday_code = request.args.get('code')
    unit_number = request.args.get('unit')
    
    print(class_code, unit_number, sunday_code)

    # if not class_code or not sunday_code or class_code not in CLASES:
    if not class_code or not sunday_code or not unit_number:
        return render_template('400.html'), 400

    code_verification_setting = Setup.query.filter_by(key='code_verification').first()
    code_verification_enabled = code_verification_setting.value if code_verification_setting else 'true'

    if code_verification_enabled == 'false':
        return render_template('attendance.html', class_code=class_code, sunday_code=sunday_code, sunday=get_next_sunday(),unit_number=unit_number)
    
    expected_code = get_next_sunday_code(get_next_sunday())
    if int(sunday_code) == expected_code:
        return render_template('attendance.html', class_code=class_code, sunday_code=sunday_code, sunday=get_next_sunday(),unit_number=unit_number)
    else:
        return render_template('403.html'), 403
    


# =============================================================================================
@bp.route('/attendances', methods=['GET', 'POST'])
@role_required('User', 'Admin', 'Owner')
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
    code_verification_setting = Setup.query.filter_by(key='code_verification').first()

    # Build the base query for attendance
    query = db.session.query(
    Attendance.id,
    Attendance.student_name,
    Classes.short_name,
    Attendance.sunday_date,
    Attendance.submit_date,
    Attendance.sunday_code,
    MeetingCenter.short_name.label('meeting_short_name')).join(Classes, Attendance.class_id == Classes.id) \
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
                code_verification_setting = Setup(key='code_verification', value=new_value)
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
    form                           = AttendanceForm()
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

        db.session.commit()
        flash('Attendance record updated successfully.', 'success')
        return redirect(url_for('routes.attendances',**request.args.to_dict()))
    return render_template('form.html', form=form, title="Editar Asistencia", submit_button_text="Actualizar", clas="warning")


# =============================================================================================
@bp.route('/attendance/delete/<int:id>', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def delete_attendance(id):
    
    attendance = Attendance.query.get_or_404(id)
    db.session.delete(attendance)
    db.session.commit()
    flash('Attendance record deleted successfully.', 'success')
    return redirect(url_for('routes.attendances', **request.args.to_dict()))

# =============================================================================================
@bp.route('/attendance/manual')
@role_required('User', 'Admin', 'Owner')
def manual_attendance():
    """Genera enlaces solo para las clases correspondientes al próximo domingo."""

    next_sunday_code = get_next_sunday_code(get_next_sunday())
    sunday_week      = (get_next_sunday().day - 1) // 7 + 1  # Determina la semana del mes
    unit             = session['meeting_center_number']
    
        
    # Generar enlaces solo para las clases correspondientes

    class_links = {
        class_entry.class_code: {
            'url': f"{Config.BASE_URL}/attendance/manual?class_name={class_entry.class_name}&class={class_entry.class_code}&code={next_sunday_code}&unit={unit}",
            'name': class_entry.class_name
        }
        for class_entry in Classes.query.all() if str(sunday_week) in class_entry.schedule.split(',')
    }

    return render_template('manual_attendance.html', class_links=class_links)
# =============================================================================================
@bp.route('/registrar', methods=['POST'])
def registrar():
    try:
        student_name        = request.form.get('studentName').title()
        nombre, apellido    = student_name.split(" ", 1)
        formatted_name      = f"{apellido}, {nombre}"
        class_code          = request.form.get('classCode')  # Usar código de clase en lugar del nombre
        sunday_date         = get_next_sunday()
        sunday_code         = request.form.get('sundayCode')
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
            class_code          = class_code,
            sunday_date         = sunday_date,
            sunday_code         = sunday_code,
            meeting_center_id   = meeting_center.id
        )
        db.session.add(new_attendance)
        db.session.commit()

        return jsonify({
            "success"     : True,
            "message"     : "Asistencia registrada exitosamente.",
            "student_name": student_name,
            "class_name"  : class_entry.class_name,
            "sunday_date" : sunday_date.strftime("%b %d, %Y")
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Hubo un error al registrar la asistencia: {str(e)}"
        }), 500


# =============================================================================================
# Rutas para la Administracion de PDF
@bp.route('/list_pdfs', methods=['GET'])
@role_required('User', 'Admin', 'Owner')
def list_pdfs():
    OUTPUT_DIR = get_output_dir()
    
    meeting_center_id = session.get('meeting_center_id')
    # Verificar si hay clases asociadas al meeting center
    has_classes       = Classes.query.filter_by(meeting_center_id=meeting_center_id, is_active=True).first() is not None
    print(f"Has Classes (Meeting Center {meeting_center_id}): {has_classes}")
    
    # Verificar si hay clases 'Main' activas
    has_main_classes  = Classes.query.filter_by(meeting_center_id=meeting_center_id, is_active=True, class_type='Main').first() is not None
    print(f"Has Main Classes (Meeting Center {meeting_center_id}): {has_main_classes}")
    
    # Verificar si hay clases 'Extra' activas
    has_extra_classes = Classes.query.filter_by(meeting_center_id=meeting_center_id, is_active=True, class_type='Extra').first() is not None
    print(f"Has Extra Classes (Meeting Center {meeting_center_id}): {has_extra_classes}")
    
    if not os.path.exists(OUTPUT_DIR):
      os.makedirs(OUTPUT_DIR)  # Crea el directorio si no existe
      
    directory = os.path.join(os.getcwd(), OUTPUT_DIR)
    pdf_files = os.listdir(directory)
    
    return render_template('list_pdfs.html', pdf_files=pdf_files, has_classes=has_classes, has_main_classes=has_main_classes, has_extra_classes=has_extra_classes)

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
@bp.route('/generate_week_pdfs', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def generate_extra_pdfs():
    return redirect(url_for('routes.generate_pdfs', type='extra'))  # redirige a la misma función para PDFs de la semana específica

# =============================================================================================
@bp.route('/generate_pdfs', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def generate_pdfs():
    
    OUTPUT_DIR = get_output_dir()
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    sunday_week = get_sunday_week(get_next_sunday())
    
    clases_a_imprimir = (
        [c.class_name for c in Classes.query.filter_by(is_active=True)]
        if request.args.get('type') == 'todos'
        else [c.class_name for c in Classes.query.filter_by(is_active=True, class_type='extra')]
        if request.args.get('type') == 'extra'
        else [c.class_name for c in Classes.query.filter_by(is_active=True) if str(sunday_week) in c.schedule.split(',')]
    )
    
    # clases_a_imprimir = (
    #     # [c.class_name for c in Classes.query.all()]
    #     [c.class_name for c in Classes.query.filter_by(is_active=True)]
    #     if request.args.get('type') == 'todos'         
    #     else [c.class_name for c in Classes.query.filter_by(is_active=True) if str(sunday_week) in c.schedule.split(',')]
    # )

    next_sunday_code = get_next_sunday_code(get_next_sunday())
    unit             = session['meeting_center_number']
    unit_name        = session['meeting_center_name']
    
    clean_qr_folder(OUTPUT_DIR)

    for class_name in clases_a_imprimir:
        class_entry = Classes.query.filter_by(class_name=class_name).first()
        if class_entry:
            class_code  = class_entry.class_code
            class_color = class_entry.class_color or "black"  # Usa el color almacenado o negro por defecto
        else:
            continue

        qr_url = f"{Config.BASE_URL}/attendance?class_name={class_name.replace(' ', '+')}&code={next_sunday_code}&unit={unit}&class={class_code}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=class_color, back_color="white")
        
        qr_filename = os.path.join(OUTPUT_DIR, f"{class_name}_{get_next_sunday()}.png")
        img.save(qr_filename)
        
        pdf_filename = os.path.join(OUTPUT_DIR, f"{class_name}_{get_next_sunday()}.pdf")
        c = canvas.Canvas(pdf_filename, pagesize=letter)
        page_width, page_height = letter
        
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor("black")
        c.drawCentredString(page_width / 2, 670, f"Lista de Asistencia")
        c.setFont("Helvetica-Bold", 35)
        c.drawCentredString(page_width / 2, 625, class_name)
        
        qr_image = ImageReader(qr_filename)
        qr_size  = 430
        qr_x     = (page_width - qr_size) / 2
        qr_y     = (page_height - qr_size) / 2
        c.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)
        
        c.setFont("Helvetica", 18)
        c.setFillColor("black")
        c.drawCentredString(page_width / 2, qr_y - 15, unit_name)
        c.drawCentredString(page_width / 2, qr_y - 40, f"{get_next_sunday().strftime('%B %d, %Y')}")
        c.save()

    clean_qr_images(OUTPUT_DIR)
    flash('QR Codes generated successfully.', 'success')
    return redirect(url_for('routes.list_pdfs'))


# =============================================================================================
@bp.route('/download_pdf/<path:filename>', methods=['GET'])
@role_required('User', 'Admin', 'Owner')
def download_pdf(filename):
    OUTPUT_DIR = get_output_dir()
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
@bp.route('/generate_qr_code/<int:user_id>', methods=['GET'])
def generate_qr_code(user_id):
    try:
        # Get the user from the database
        user = User.query.get(user_id)
        if not user:
            flash("User not found", "danger")
            return redirect(url_for('routes.users'))

        # Generate token
        token = generate_token(user.id)

        # Construct the login URL with the token and redirect URL
        login_url = f"{Config.BASE_URL}/login?token={token}&next=/attendance/manual"

        # Generate QR code
        qr = qrcode.make(login_url)

        # Save QR code to memory
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)

        # Return the QR code as a file response
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='login_qr_code.png')

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for('routes.users'))


# =============================================================================================
# CRUD para Meeting Centers
@bp.route('/meeting_centers/', methods=['GET', 'POST'])
@role_required('Owner')
def meeting_centers():
    meeting_centers    = MeetingCenter.query.all()
    main_classes_exist = {mc.id: Classes.query.filter_by(meeting_center_id=mc.id, class_type='Main').count() > 0 for mc in meeting_centers}
    return render_template('meeting_centers.html', meeting_centers=meeting_centers, main_classes_exist=main_classes_exist)
    
@bp.route('/meeting_center/new', methods=['GET', 'POST'])
@role_required('Owner')
def create_meeting_center():
    form = MeetingCenterForm()
    if form.validate_on_submit():
        new_center     = MeetingCenter(
            unit_number=form.unit_number.data,
            name       =form.name.data,
            short_name =form.short_name.data,
            city       =form.city.data,
            start_time =form.start_time.data,
            end_time   =form.end_time.data
        )
        db.session.add(new_center)
        db.session.commit()
        flash('Meeting center created successfully!', 'success')
        return redirect(url_for('routes.meeting_centers'))
    return render_template('form.html', form=form, title="Create new Meeting center", submit_button_text="Create", clas="warning")


# =============================================================================================
@bp.route('/meeting_center/edit/<int:id>', methods=['GET', 'POST'])
@role_required('Owner')
def update_meeting_center(id):
    meeting_center = MeetingCenter.query.get_or_404(id)
    form           = MeetingCenterForm(obj=meeting_center)
    if form.validate_on_submit():
        form.populate_obj(meeting_center)
        db.session.commit()
        flash('Meeting Center updated successfully.', 'success')
        return redirect(url_for('routes.meeting_centers'))
    return render_template('form.html', form=form, title="Edit Meeting Center", submit_button_text="Update", clas="warning")


# =============================================================================================
@bp.route('/meeting_center/delete/<int:id>', methods=['POST'])
@role_required('Admin', 'Owner')
def delete_meeting_center(id):
    meeting_center = MeetingCenter.query.get_or_404(id)
    if meeting_center.attendances:
        flash('The meeting center cannot be deleted because it has registered attendance.', 'danger')
        return redirect(url_for('routes.meeting_centers'))
    
    db.session.delete(meeting_center)
    db.session.commit()
    flash('Meeting Center successfully removed.', 'success')
    return redirect(url_for('routes.meeting_centers'))


# =============================================================================================
@bp.route('/classes', methods=['GET'])
@role_required('Admin', 'Owner')
def classes():
    # Get user role and meeting_center_id from session
    role = session.get('role')
    meeting_center_id = session.get('meeting_center_id')
    
    query = db.session.query(
        Classes.id,
        Classes.class_name,
        Classes.short_name,
        Classes.class_code,
        Classes.class_type,
        Classes.schedule,
        Classes.is_active,
        Classes.class_color,
        MeetingCenter.short_name.label('meeting_short_name')
        ).join(MeetingCenter, Classes.meeting_center_id == MeetingCenter.id)

    if role == 'Admin':
        query = query.filter(Classes.meeting_center_id == meeting_center_id)
    elif role == 'Owner':
        pass
    
    
    classes = query.all()

    return render_template('classes.html', classes=classes)
# =============================================================================================

@bp.route('/classes/new', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def create_class():
    form = ClassForm()
    form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]
    
    if form.validate_on_submit():
        new_class = Classes(
            class_name=form.class_name.data,
            short_name=form.short_name.data,
            class_code=form.class_code.data,
            class_type=form.class_type.data,
            schedule=form.schedule.data,
            is_active=form.is_active.data,
            class_color=form.class_color.data,
            meeting_center_id=form.meeting_center_id.data
        )
        try:
            db.session.add(new_class)
            db.session.commit()
            flash('Class created successfully!', 'success')
            return redirect(url_for('routes.classes'))
        except IntegrityError:
            db.session.rollback()
            flash('A class with this name, short name, or code already exists in the same meeting center.', 'danger')
    return render_template('form.html', form=form, title="Create New Class", submit_button_text="Create", clas="warning")

# =============================================================================================
@bp.route('/classes/edit/<int:id>', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def update_class(id):
    class_instance = Classes.query.get_or_404(id)
    form = ClassForm(obj=class_instance)
    form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]
    
    if form.validate_on_submit():
        class_instance.class_name           = form.class_name.data
        class_instance.short_name           = form.short_name.data
        class_instance.class_code           = form.class_code.data
        class_instance.class_type           = form.class_type.data
        class_instance.schedule             = form.schedule.data
        class_instance.is_active            = form.is_active.data
        class_instance.class_color          = form.class_color.data
        class_instance.meeting_center_id    = form.meeting_center_id.data
        try:
            db.session.commit()
            flash('Class updated successfully!', 'success')
            return redirect(url_for('routes.classes'))
        except IntegrityError:
            db.session.rollback()
            flash('A class with this name, short name, or code already exists in the same meeting center.', 'danger')
    return render_template('form.html', form=form, title="Edit Class", submit_button_text="Update", clas="warning")


# =============================================================================================
@bp.route('/classes/delete/<int:id>', methods=['POST'])
@role_required('Admin', 'Owner')
def delete_class(id):
    class_instance = Classes.query.get_or_404(id)
    if class_instance.attendances:
        flash('No se puede eliminar la clase porque tiene asistencias registradas.', 'danger')
        return redirect(url_for('routes.classes'))
    if class_instance.class_type == 'main':
        flash('Cannot delete a main class.', 'warning')
        return redirect(url_for('routes.classes'))
    try:
        db.session.delete(class_instance)
        db.session.commit()
        flash('Class deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting class: {e}', 'danger')
    return redirect(url_for('routes.classes'))

# =============================================================================================
# @bp.route('/classes/populate/<int:id>', methods=['GET', 'POST'])
# @role_required('Owner')
# def populate_classes(id):
#     new_meeting_center_id = id
#     try:
#         existing_classes = Classes.query.filter_by(meeting_center_id=new_meeting_center_id).first()
#         if existing_classes:
#             flash("Classes already exist for this meeting center", "Warning", "danger")
#             return

#         main_classes = Classes.query.filter_by(class_type='Main').all()
#         for main_class in main_classes:
#             duplicate_class      = Classes(
#                 class_name       =main_class.class_name,
#                 short_name       =main_class.short_name,
#                 class_code       =main_class.class_code,
#                 class_type       =main_class.class_type,
#                 schedule         =main_class.schedule,
#                 is_active        =main_class.is_active,
#                 class_color      =main_class.class_color,
#                 meeting_center_id=new_meeting_center_id
#             )
#             db.session.add(duplicate_class)
# #         # Confirmar los cambios en la base de datos
#         db.session.commit()
#         flash("Main classes successfully populated.", "success")
#     except IntegrityError as ie:
#         db.session.rollback()
#         flash(f"Unique constraint error: {str(ie)}", "danger")
#     except Exception as e:
#         db.session.rollback()
#         raise ValueError(f"Error duplicating main classes for new meeting center: {str(e)}")
    
#     return redirect(url_for('routes.meeting_centers'))  # Redirige a una vista después de completar la operación



@bp.route('/classes/populate/<int:id>', methods=['GET', 'POST'])
@role_required('Owner')
def populate_classes(id):
    new_meeting_center_id = id

    # Arreglo estático con las clases tipo Main
    main_classes_static = [
        {
            "class_name": "Elders Quorum",
            "short_name": "Elders_Q",
            "class_code": "EQ",
            "class_type": "Main",
            "schedule"  : "2,4",
            "is_active" : True,
            "class_color": None  # Esto se puede ajustar en el futuro
        },
        {
            "class_name": "Aaronic Priesthood",
            "short_name": "Aaronic_P",
            "class_code": "AP",
            "class_type": "Main",
            "schedule"  : "2,4",
            "is_active" : True,
            "class_color": None
        },
        {
            "class_name": "Relief Society",
            "short_name": "Relief_S",
            "class_code": "RS",
            "class_type": "Main",
            "schedule"  : "2,4",
            "is_active" : True,
            "class_color": "#ba8e23"
        },
        {
            "class_name": "Young Woman",
            "short_name": "Young_W",
            "class_code": "YW",
            "class_type": "Main",
            "schedule"  : "2,4",
            "is_active" : True,
            "class_color": "#943f88"
        },
        {
            "class_name": "Sunday School - Adults",
            "short_name": "S_S_Adults",
            "class_code": "SSA",
            "class_type": "Main",
            "schedule"  : "1,3",
            "is_active" : True,
            "class_color": None
        },
        {
            "class_name": "Sunday School - Youth",
            "short_name": "S_S_Youth",
            "class_code": "SSY",
            "class_type": "Main",
            "schedule"  : "1,3",
            "is_active" : True,
            "class_color": None
        },
        {
            "class_name": "Fifth Sunday",
            "short_name": "F_Sunday",
            "class_code": "FS",
            "class_type": "Main",
            "schedule"  : "5",
            "is_active" : True,
            "class_color": None
        }
    ]

    try:
        # Validar si ya existen clases asociadas al nuevo Meeting Center
        existing_classes = Classes.query.filter_by(meeting_center_id=new_meeting_center_id).first()
        if existing_classes:
            flash("Classes already exist for this meeting center", "warning")
            return redirect(url_for('routes.meeting_centers'))

        # Insertar las clases del arreglo estático
        for class_data in main_classes_static:
            new_class = Classes(
                class_name=class_data["class_name"],
                short_name=class_data["short_name"],
                class_code=class_data["class_code"],
                class_type=class_data["class_type"],
                schedule=class_data["schedule"],
                is_active=class_data["is_active"],
                class_color=class_data["class_color"],
                meeting_center_id=new_meeting_center_id
            )
            db.session.add(new_class)

        # Confirmar los cambios en la base de datos
        db.session.commit()
        flash("Main classes successfully populated.", "success")

    except IntegrityError as ie:
        db.session.rollback()
        flash(f"Unique constraint error: {str(ie)}", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error duplicating main classes for new meeting center: {str(e)}", "danger")

    return redirect(url_for('routes.meeting_centers'))




# =============================================================================================
@bp.route('/organizations', methods=['GET'])
def organizations():
    organizations = Organization.query.all()
    return render_template('organizations.html', organizations=organizations)

# =============================================================================================
@bp.route('/organizations/new', methods=['GET', 'POST'])
def create_organization():
    form = OrganizationForm()
    if form.validate_on_submit():
        new_org = Organization(name=form.name.data)
        try:
            db.session.add(new_org)
            db.session.commit()
            flash('Organization created successfully!', 'success')
            return redirect(url_for('routes.organizations'))
        except Exception as e:
            db.session.rollback()
            flash('Error: Organization name must be unique.', 'danger')
            return redirect(url_for('routes.organizations'))
    return render_template('form.html', form=form, title="Create new Organization", submit_button_text="Create", clas="warning")


# Update
@bp.route('/organizations/edit/<int:id>', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def edit_organization(id):
    organization = Organization.query.get_or_404(id)
    form         = OrganizationForm(obj=organization)
    if form.validate_on_submit():
        organization.name = form.name.data
        try:
            db.session.commit()
            flash('Organization updated successfully!', 'success')
            return redirect(url_for('routes.organizations'))
        except Exception as e:
            db.session.rollback()
            flash('Error: Organization name must be unique.', 'danger')
    return render_template('form.html', form=form, title="Edit Organization", submit_button_text="Update", clas="warning", organization=organization)

# Delete
@bp.route('/organizations/delete/<int:id>', methods=['POST'])
def delete_organization(id):
    organization = Organization.query.get_or_404(id)
    try:
        db.session.delete(organization)
        db.session.commit()
        flash('Organization deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error: Could not delete organization.', 'danger')
    return redirect(url_for('routes.organizations'))