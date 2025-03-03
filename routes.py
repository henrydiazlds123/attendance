import csv
import io
import qrcode
from flask                   import Blueprint, Response, abort, jsonify, render_template, redirect, request, session, url_for, flash, send_from_directory
from flask_babel             import gettext as _
from sqlalchemy              import func, extract, desc, asc
from sqlalchemy.orm          import joinedload
from sqlalchemy.exc          import IntegrityError
from config                  import Config
from models                  import db, Classes, User, Attendance, MeetingCenter, Setup, Organization, NameCorrections
from forms                   import AttendanceEditForm, AttendanceForm, MeetingCenterForm, UserForm, EditUserForm, ResetPasswordForm, ClassForm, OrganizationForm, ProfileForm
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils     import ImageReader
from reportlab.pdfgen        import canvas
from urllib.parse            import unquote
from utils                   import *
from datetime                import datetime, timedelta
from collections             import defaultdict

bp = Blueprint('routes', __name__)

@bp.before_request
def load_user():
    # Verifica si el usuario está en sesión
    user_id = session.get('user_id')

    # Si no hay sesión, revisa la cookie 'remember_me'
    if not user_id:
        user_id = request.cookies.get('remember_me')

    if user_id:
        user = User.query.get(user_id)
        if user:
            g.user                       = user
            session['user_id']           = user.id
            session['user_name']         = user.name
            session['role']              = user.role
            session['meeting_center_id'] = user.meeting_center_id
            session['organization_id']   = user.organization_id
        else:
            g.user = None
    else:
        g.user = None


# =============================================================================================
@bp.route('/login', methods=['GET', 'POST'])
def login():

    next_url = request.args.get('next')

    if request.method == 'POST':
        username    = request.form['username']
        password    = request.form['password']
        remember_me = request.form.get('remember_me') == 'on'

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            meeting_center                   = MeetingCenter.query.get(user.meeting_center_id)
            session['user_id']               = user.id
            session['user_name']             = user.name
            session['username']              = user.username
            session['user_lastname']         = user.lastname
            session['user_email']            = user.email
            session['role']                  = user.role  # Guarda el rol del usuario
            session['meeting_center_id']     = meeting_center.id
            session['meeting_center_name']   = meeting_center.name
            session['meeting_center_number'] = meeting_center.unit_number
            session['organization_id']       = user.organization_id
            
            # Si "Remember Me" está marcado, guarda la cookie
            response = redirect(next_url or url_for('routes.attendance_report'))
            if remember_me:
                response.set_cookie('remember_me', str(user.id), max_age=2*24*60*60)  # 30 días
            return response

        flash(_('Invalid credentials. Please check your username and password.'), 'danger')

    return render_template('login.html')


# =============================================================================================
@bp.route('/logout')
def logout():
    session.clear()
    response = redirect(url_for('routes.login'))
    response.delete_cookie('remember_me')  # Elimina la cookie al cerrar sesión
    flash(_('Logout successful!'), 'success')
    return response


# =============================================================================================
@bp.route('/reset_name')
def reset_name():
    """Renderiza una página para mostrar el nombre almacenado y borrarlo con confirmación."""
    return render_template('reset_name.html')


# =============================================================================================
@bp.route('/')
def index():
    #return render_template('index.html')
    return redirect('/login', code=302)


# =============================================================================================
@bp.route('/users')
@role_required('Admin', 'Super', 'Owner')
def users():
    role = session.get('role')
    meeting_center_id = get_meeting_center_id()
    organization_id = session.get('organization_id')  # Agregamos la organización del usuario actual
    admin_count = User.query.filter_by(role='Admin').count()

    query = db.session.query(
        User.id,
        User.username,
        User.email,
        User.role,
        MeetingCenter.short_name.label('meeting_short_name'),
        Organization.name.label('organization_name')
    ).join(MeetingCenter, User.meeting_center_id == MeetingCenter.id) \
     .join(Organization, User.organization_id == Organization.id)

    if role == 'Owner': # El Owner ve todos si el meeting_center_id es 'all'       
        if meeting_center_id != 'all': 
            query = query.filter(User.meeting_center_id == meeting_center_id)
        query = query.filter((User.role != 'Owner') | (User.username == session.get('username')))
    elif role == 'Super': # Super ve solo usuarios de su organización        
        query = query.filter(User.organization_id == organization_id).filter((User.role != 'Owner') | (User.username == session.get('username')))
    elif role == 'Admin': # Admin ve solo usuarios de su propio Meeting Center, excluyendo Owners        
        query = query.filter(User.meeting_center_id == meeting_center_id).filter(User.role != 'Owner')
    else:
        # Usuario regular solo ve su propio usuario
        query = db.session.query(
            User.id,
            User.username,
            User.email,
            User.role,
            MeetingCenter.short_name.label('meeting_short_name'),
            Organization.name.label('organization_name')
        ).join(MeetingCenter, User.meeting_center_id == MeetingCenter.id) \
         .join(Organization, User.organization_id == Organization.id) \
         .filter(User.username == session.get('username'))

    users = query.order_by(asc(User.meeting_center_id), asc(User.organization_id), asc(User.role)).all()

    return render_template('users.html', users=users, admin_count=admin_count)


# =============================================================================================
@bp.route('/user/new', methods=['GET', 'POST'])
@role_required('Admin', 'Super', 'Owner')
def create_user():

    form                           = UserForm()
    form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]
    form.organization_id.choices   = [(og.id, og.translated_name) for og in Organization.query.all()]

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
    return render_template('form.html', form=form, title=_('New User'), submit_button_text=_('Create'), clas='warning')


# =============================================================================================
@bp.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def update_user(id):
    user                           = User.query.get_or_404(id)
    form                           = EditUserForm(obj=user)
    form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]
    form.organization_id.choices   = [(og.id, og.translated_name) for og in Organization.query.all()]

    if form.validate_on_submit():
        user.username          = form.username.data
        user.email             = form.email.data
        user.name              = form.name.data
        user.lastname          = form.lastname.data
        user.role              = form.role.data
        user.meeting_center_id = form.meeting_center_id.data
        user.is_active         = form.is_active.data

        db.session.commit()
        flash(_('User updated successfully.'), 'success')
        return redirect(url_for('routes.users'))
    return render_template('form.html',
                           form               = form,
                           title              = _('Edit User'),
                           submit_button_text = _('Update'),
                           clas               = 'warning')


# =============================================================================================
@bp.route('/user/delete/<int:id>', methods=['POST'])
@role_required('Admin', 'Super', 'Owner')  # Solo los admins pueden acceder a esta ruta
def delete_user(id):
    user_to_delete = User.query.get_or_404(id)
    current_user_id = session.get('user_id')
    current_user_role = session.get('role')

    # Contar cuántos admins existen en total
    admin_count = User.query.filter_by(role='Admin').count()

    # Verificar si el usuario actual es Owner
    if current_user_role == 'Owner':
        if user_to_delete.role == 'Admin' and admin_count <= 1:
            flash(_('Cannot delete last admin.'), 'danger')
            return redirect(url_for('routes.users'))
        
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(_('User deleted successfully'), 'success')
        return redirect(url_for('routes.users'))

    # Los Admin no pueden eliminar a otros Admin
    if user_to_delete.role == 'Admin':
        flash(_('You cannot delete another administrator.'), 'danger')
        return redirect(url_for('routes.users'))

    # Los Admin pueden eliminar a un usuario común (User)
    if current_user_id == user_to_delete.id:  # Permitir que un admin se elimine a sí mismo
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(_('You have successfully eliminated yourself.'), 'success')
        return redirect(url_for('auth.login'))  # Redirigir a la página de login

    db.session.delete(user_to_delete)
    db.session.commit()
    flash(_('User deleted successfully'), 'success')
    return redirect(url_for('routes.users'))


# =============================================================================================
@bp.route('/users/<int:id>/reset_password', methods=['GET', 'POST'])
def reset_password(id):
    user = User.query.get_or_404(id)
    form = ResetPasswordForm()

    if form.validate_on_submit():
        if not user.check_password(form.current_password.data):
            flash(_('Current password is incorrect.'), 'danger')
            return render_template('form.html', 
                                   form               = form,
                                   title              = "Reset Password",
                                   submit_button_text = "Update",
                                   clas               = "danger")

        user.set_password(form.new_password.data)
        db.session.commit()
        flash(_('Password updated successfully.'), 'success')
        return redirect(url_for('routes.users'))

    return render_template('form.html', 
                           form               = form,
                           title              = "Change Password",
                           submit_button_text = "Update",
                           clas               = "danger")


# =============================================================================================
@bp.route('/users/<int:id>/promote', methods=['POST'])
@role_required('Owner', 'Admin')
def promote_to_super(id):
    user = User.query.get_or_404(id)
    if user.role =='Super':
        flash(_('The user is already an Super User.'), 'info')
    else:
        user.role = 'Super'
        db.session.commit()
        # flash(f'El usuario {user.username} ha sido promovido a administrador.', 'success')
        flash(_('User %(username)s has been promoted to Super User.') % {'username': user.username}, 'success')
    return redirect(url_for('routes.users'))


# =============================================================================================
@bp.route('/attendance', methods=['GET', 'POST'])
def attendance():
    class_code  = request.args.get('classCode')
    sunday_code = request.args.get('sundayCode')
    unit_number = request.args.get('unitNumber')
    
    # if not class_code or not sunday_code or class_code not in CLASES:
    if not class_code or not sunday_code or not unit_number:
        return render_template('4xx.html', 
                               page_title    = _('400 Invalid URL'),
                               error_number  = '400',
                               error_title   = _(_('Check what you wrote!')),
                               error_message = _('The address you entered is incomplete!')), 400

    code_verification_setting = Setup.query.filter_by(key='code_verification').first()
    code_verification_enabled = code_verification_setting.value if code_verification_setting else 'true'

    if code_verification_enabled == 'false':
        return render_template('attendance.html', 
                               class_code  = class_code,
                               sunday_code = sunday_code,
                               sunday      = get_next_sunday(),
                               unit_number = unit_number)
    
    expected_code = get_next_sunday_code(get_next_sunday())
    if int(sunday_code) == expected_code:
        return render_template('attendance.html', 
                               class_code  = class_code,
                               sunday_code = sunday_code,
                               sunday      = get_next_sunday(),
                               unit_number = unit_number)
    else:
        return render_template('4xx.html', 
                               page_title    = '403 Incorrect QR',
                               error_number  = '403',
                               error_title   = _('It seems that you are lost!'),
                               error_message = _("Wrong QR for this week's classes!")), 403
    

# =============================================================================================
@bp.route('/attendance/list', methods=['GET', 'POST'])
@login_required
def attendances():
    # Get user role and meeting_center_id from session
    role              = session.get('role')
    months_abr        = get_months()
    meeting_center_id = get_meeting_center_id()
    corrected_names   = [
        correction.correct_name 
        for correction in NameCorrections.query.filter_by(meeting_center_id=meeting_center_id).all()
    ]

    # Get distinct values for filters
    if meeting_center_id == 'all':
        classes = db.session.query(db.func.min(Classes.id).label("id"),Classes.short_name).join(Attendance, Attendance.class_id == Classes.id).group_by(Classes.short_name).all()
        students = db.session.query(Attendance.student_name.distinct()).all()
        sundays  = db.session.query(Attendance.sunday_date.distinct()).order_by(Attendance.sunday_date.desc()).all()
    else:    
        classes  = db.session.query(Classes.id, Classes.short_name).join(Attendance, Attendance.class_id == Classes.id).distinct().filter(Classes.meeting_center_id == meeting_center_id).all()
        students = db.session.query(Attendance.student_name.distinct()).filter(Attendance.meeting_center_id == meeting_center_id).all()
        sundays  = db.session.query(Attendance.sunday_date.distinct()).filter(Attendance.meeting_center_id == meeting_center_id).order_by(Attendance.sunday_date.desc()).all()

    # Formatear las fechas con Flask-Babel
    sundays_formatted = [
        {"date": sunday[0], "formatted": format_date(sunday[0], format='MMM dd')}  # 'MMM dd' para "Mes día"
        for sunday in sundays
    ]

    # Get filter parameters from URL query string
    class_name    = request.args.get('class_name')
    student_name  = request.args.get('student_name')
    sunday_date   = request.args.get('sunday_date')
    page          = request.args.get('page', 1, type=int)
    per_page      = request.args.get('per_page', 150, type=int)

    query = db.session.query(
        Attendance.id,
        Attendance.student_name,
        Classes.short_name.label('class_short_name'),
        Attendance.class_code,
        Attendance.sunday_date,
        Attendance.submit_date,
        Attendance.sunday_code,
        Attendance.meeting_center_id,
        MeetingCenter.short_name.label('meeting_short_name')
    ).join(
        Classes, 
        (Attendance.class_code == Classes.class_code) & (Attendance.meeting_center_id == Classes.meeting_center_id)
    ).join(
        MeetingCenter, 
        Attendance.meeting_center_id == MeetingCenter.id
    )
    
    sundays = db.session.query(Attendance.sunday_date.distinct()) \
    .filter(Attendance.meeting_center_id == session.get('meeting_center_id')).all()

    years = db.session.query(func.strftime('%Y', Attendance.sunday_date).label('year')) \
    .filter(Attendance.meeting_center_id == session.get('meeting_center_id')).distinct().all()

    months = db.session.query(func.strftime('%m', Attendance.sunday_date).label('month')) \
    .filter(Attendance.meeting_center_id == session.get('meeting_center_id')).distinct().all()

    # Filter based on role and meeting_center_id
    if role == 'Admin' or role == 'User':
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
    if meeting_center_id == 'all':
        attendances = query.order_by(asc(Attendance.student_name), desc(Attendance.sunday_date), Attendance.class_id).paginate(page=page, per_page=per_page, error_out=False)
    else:
        attendances = query.order_by(asc(Attendance.student_name), desc(Attendance.sunday_date), Attendance.class_id) \
            .filter(Attendance.meeting_center_id == session.get('meeting_center_id')).paginate(page=page, per_page=per_page, error_out=False)

    # Formatear las fechas con Flask-Babel
    attendances_formatted = [
        {
            **attendance._asdict(),  # Convertir el objeto SQLAlchemy a un diccionario
            "sunday_date_formatted": format_date(attendance.sunday_date, format='MMM dd')  # Formatear la fecha
        }
        for attendance in attendances.items
    ]

    total_registros = attendances.total
    has_records = total_registros > 0

   # For AJAX requests, return only the table partial
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template(
            'partials/tables/attendance_list_table.html',
            attendances     = attendances_formatted,
            has_records     = has_records,
            total_registros = total_registros,
            corrected_names = corrected_names,
            pagination      = attendances
        )
    else:
        # Si no es AJAX, renderizar la plantilla completa
        return render_template(
            'attendance_list.html',
            attendances     = attendances_formatted,
            has_records     = has_records,
            classes         = classes,
            students        = students,
            sundays         = sundays_formatted,
            months          = months,
            years           = years,
            total_registros = total_registros,
            months_abr      = months_abr,
            corrected_names = corrected_names,
            pagination      = attendances
        )
# =============================================================================================
@bp.route('/attendance/new', methods=['GET', 'POST'])
@role_required('Admin', 'Super', 'Owner')
def create_attendance():
    meeting_center_id = get_meeting_center_id()
    form                           = AttendanceForm()
    form.class_id.choices          = [(c.id, c.translated_name) for c in Classes.query.filter_by(meeting_center_id=meeting_center_id).all()]
    form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]

    if request.method == 'GET':
        form.set_default_sunday_date() 

    # Populate student name choices dynamically with current student names
    existing_students          = db.session.query(Attendance.student_name).filter(Attendance.meeting_center_id == session['meeting_center_id']).distinct().all()
    form.student_name.choices += [(name[0], name[0]) for name in existing_students]
    
    if form.validate_on_submit(): # Determine whether to use an existing student name or a new one       
        student_name = form.new_student_name.data.strip() if form.new_student_name.data else form.student_name.data
        if not student_name: # Check if no name was provided in either field
            flash(_('Please select an existing student or provide a new name.'), 'danger')
            return render_template('form.html', 
                                   form               = form,
                                   title              = _('Create manual attendance'),
                                   submit_button_text = _('Create'),
                                   clas               = 'warning')

        sunday_code = '0000' # Indica que la clase fue entrada manualmente, no usando QR 

        # Obtener el class_code basado en el class_id seleccionado
        selected_class = Classes.query.filter_by(id=form.class_id.data).first()
        if not selected_class:
            flash(_('The selected class is invalid.'), 'danger')
            return render_template('form.html', 
                                   form               = form,
                                   title              = _('Create attendance'),
                                   submit_button_text = _('Create'),
                                   clas               = 'warning')

        attendance = Attendance(
            student_name     = student_name,
            class_id         = form.class_id.data,
            class_code       = selected_class.class_code,  # Asignar el class_code
            sunday_date      = form.sunday_date.data,
            sunday_code      = sunday_code,
            meeting_center_id= form.meeting_center_id.data
        )
        db.session.add(attendance)
        db.session.commit()
        flash(_('Attendance registered successfully!'))
        return redirect(url_for('routes.attendances'))

    return render_template('form.html', 
                           form               = form,
                           title              = _('Create manual attendance'),
                           submit_button_text = _('Create'),
                           clas               = 'warning')


# =============================================================================================
@bp.route('/attendance/edit/<int:id>', methods=['GET', 'POST'])
@role_required('Admin', 'Super', 'Owner')
def update_attendance(id):
    attendance        = Attendance.query.get_or_404(id)
    form              = AttendanceEditForm(obj=attendance)
    meeting_center_id = get_meeting_center_id()

    # Filtrar las clases por el meeting_center_id
    form.class_id.choices = [(c.id, c.translated_name) for c in Classes.query.filter_by(meeting_center_id=meeting_center_id).all()]

    if form.validate_on_submit():
        attendance.student_name = form.student_name.data
        attendance.class_id = form.class_id.data
        attendance.sunday_date = form.sunday_date.data

        # Obtener el nuevo class_code basado en el class_id seleccionado
        new_class = Classes.query.get(form.class_id.data)
        if new_class:
            attendance.class_code = new_class.class_code

        db.session.commit()
        flash(_('Attendance record updated successfully.'), 'success')
        return redirect(url_for('routes.attendances', **request.args.to_dict()))

    return render_template('form.html', form=form, title=_('Edit Attendance'), submit_button_text=_('Update'), clas='warning')


# =============================================================================================
@bp.route('/attendance/delete/<int:id>', methods=['GET', 'POST'])
@role_required('Admin', 'Super', 'Owner')
def delete_attendance(id):
    
    attendance = Attendance.query.get_or_404(id)
    db.session.delete(attendance)
    db.session.commit()
    flash(_('Attendance record deleted successfully.'), 'success')
    return redirect(url_for('routes.attendances', **request.args.to_dict()))


# =============================================================================================
@bp.route('/attendance/manual')
@login_required
def manual_attendance():
    """Genera enlaces solo para las clases correspondientes al próximo domingo."""
    next_sunday_code = get_next_sunday_code(get_next_sunday())
    sunday_week      = (get_next_sunday().day - 1) // 7 + 1  # Determina la semana del mes
    unit             = session['meeting_center_number']
        
    # Generar enlaces solo para las clases correspondientes
    class_links = {
        class_entry.class_code: {
            'url': f"{Config.BASE_URL}/attendance/manual?className={class_entry.translated_name}&classCode={class_entry.class_code}&sundayCode={next_sunday_code}&unitNumber={unit}",
            'name': class_entry.class_name
        }
        for class_entry in Classes.query.filter_by(is_active=True).all() if str(sunday_week) in class_entry.schedule.split(',')
    }
    return render_template('attendance_manual.html', class_links=class_links)


# =============================================================================================
@bp.route('/attendance/report')
@login_required
def attendance_report():
    meeting_center_id = get_meeting_center_id()
    if meeting_center_id == 'all':
        meeting_center_id = None  # No aplicar filtro

    current_year = datetime.now().year
    current_month = datetime.now().month

    selected_class = request.args.get('class', default='all')

    # Obtener clases disponibles
    class_query = db.session.query(Classes).filter(Classes.is_active == True)
    if meeting_center_id is not None:
        class_query = class_query.filter(Classes.meeting_center_id == meeting_center_id)

    available_classes = class_query.order_by(Classes.class_name).filter(Classes.meeting_center_id == meeting_center_id).all()

    selected_year = request.args.get('year', type=int, default=current_year)
    
    current_quarter = f"Q{(current_month - 1) // 3 + 1}" # Calcular el trimestre actual

    # Si no se selecciona un trimestre, por defecto usar el trimestre actual
    selected_month = request.args.get('month', default=current_quarter)

    # Determinar el filtro de mes o trimestre
    month_filter = []
    if selected_month == "all":
        month_filter = list(range(1, 13))  # Todos los meses
    elif selected_month.startswith("Q"):
        quarter_map = {"Q1": [1, 2, 3], "Q2": [4, 5, 6], "Q3": [7, 8, 9], "Q4": [10, 11, 12]}
        month_filter = quarter_map.get(selected_month, [])
    else:
        month_filter = [int(selected_month)]  # Mes específico

    # Obtener años y meses disponibles
    year_query  = db.session.query(func.extract('year', Attendance.sunday_date)).distinct().order_by(func.extract('year', Attendance.sunday_date))
    month_query = db.session.query(func.extract('month', Attendance.sunday_date)).distinct().order_by(func.extract('month', Attendance.sunday_date))

    if meeting_center_id is not None:
        year_query  = year_query.filter(Attendance.meeting_center_id == meeting_center_id)
        month_query = month_query.filter(Attendance.meeting_center_id == meeting_center_id)

    available_years  = [y[0] for y in year_query.all() if y[0] is not None]
    available_months = [m[0] for m in month_query.all() if m[0] is not None]
    month_names      = [{"num": m, "name": _(datetime(2000, m, 1).strftime('%b'))} for m in available_months]

    # Obtener fechas de domingos filtradas
    query = db.session.query(Attendance.sunday_date).distinct().order_by(Attendance.sunday_date)
    if meeting_center_id is not None:
        query = query.filter(Attendance.meeting_center_id == meeting_center_id)

    query        = query.filter(extract('year', Attendance.sunday_date) == selected_year)
    query        = query.filter(extract('month', Attendance.sunday_date).in_(month_filter))
    sundays      = query.all()
    sunday_dates = [s[0] for s in sundays][-14:]  # Limitar a los últimos 14 domingo en un trimestre

    # Formatear fechas
    sunday_dates_formatted = [
        {"date": date, "formatted": format_date(date, format='MMM dd')}
        for date in sunday_dates
    ]

    # Obtener registros de asistencia filtrados
    attendance_query = db.session.query(Attendance).order_by(Attendance.student_name, Attendance.sunday_date)
    if meeting_center_id is not None:
        attendance_query = attendance_query.filter(Attendance.meeting_center_id == meeting_center_id)
    attendance_query = attendance_query.filter(extract('year', Attendance.sunday_date) == selected_year)
    attendance_query = attendance_query.filter(extract('month', Attendance.sunday_date).in_(month_filter))

    if selected_class != 'all':
        # Obtener los nombres de los estudiantes que asistieron a la clase seleccionada
        student_names = (db.session.query(Attendance.student_name).filter(Attendance.class_code == selected_class, Attendance.meeting_center_id == meeting_center_id)).distinct().all()

        # Extraer los nombres en una lista
        student_names = [name[0] for name in student_names]

        # Filtrar attendance_query para incluir todas las asistencias de esos estudiantes
        if student_names:
            attendance_query = attendance_query.filter(Attendance.student_name.in_(student_names))

    attendance_records = attendance_query.all()

    # Procesar asistencia
    students = {}
    for record in attendance_records:
        if record.student_name not in students:
            students[record.student_name] = {date['date']: False for date in sunday_dates_formatted}
        students[record.student_name][record.sunday_date] = True

    total_miembros = len(students)

    # Si el usuario no ha seleccionado nada, debe coincidir con el mes actual
    if selected_month == "all" or selected_month not in ["Q1", "Q2", "Q3", "Q4"] + [str(m["num"]) for m in month_names]:
        selected_month = current_quarter  # Asegurar que el select refleje el trimestre actual

    # Obtener registros de asistencia por trimestre
    quarters_with_data = {
        "Q1": db.session.query(Attendance).filter(extract('month', Attendance.sunday_date).in_([1, 2, 3]),
            Attendance.meeting_center_id == meeting_center_id).count() > 0,
        "Q2": db.session.query(Attendance).filter(extract('month', Attendance.sunday_date).in_([4, 5, 6]),
            Attendance.meeting_center_id == meeting_center_id).count() > 0,
        "Q3": db.session.query(Attendance).filter(extract('month', Attendance.sunday_date).in_([7, 8, 9]),
            Attendance.meeting_center_id == meeting_center_id).count() > 0,
        "Q4": db.session.query(Attendance).filter(extract('month', Attendance.sunday_date).in_([10, 11, 12]),
            Attendance.meeting_center_id == meeting_center_id).count() > 0
    }

    # Respuesta AJAX parcial
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template(
            "partials/tables/attendance_table.html", 
            students       = students,
            dates          = sunday_dates_formatted,
            total_miembros = total_miembros
        )

    return render_template(
        'attendance_report.html',
        students           = students ,
        dates              = sunday_dates_formatted ,
        available_years    = available_years ,
        available_months   = month_names ,
        selected_year      = selected_year ,
        selected_month     = selected_month ,
        total_miembros     = total_miembros ,
        quarters_with_data = quarters_with_data ,     # Pasar los trimestres con datos
        disable_month      = len(available_months)  == 1,
        disable_year       = len(available_years)   == 1,
        available_classes  = available_classes)  # Pasar clases disponibles a la plantilla


# =============================================================================================
@bp.route('/attendance/export', methods=['GET'])
@role_required('Owner')
def export_attendance():
    # Obtener la fecha actual en formato YYYY-MM-DD para el nombre del archivo
    current_date = datetime.now().strftime('%Y-%m-%d')
    filename = f"attendance_{current_date}.csv"

    # Obtener los parámetros de filtro de la solicitud (si existen)
    filter_date = request.args.get('date')  # Fecha en formato YYYY-MM-DD
    filter_meeting_center = request.args.get('meeting_center_id')  # ID de centro de reunión

    # Convertir la fecha de filtro en un objeto datetime, si se proporcionó
    if filter_date:
        filter_date = datetime.strptime(filter_date, '%Y-%m-%d').date()

    # Crear una consulta con filtros opcionales
    query = Attendance.query

    if filter_date:
        query = query.filter(Attendance.sunday_date == filter_date)

    if filter_meeting_center:
        query = query.filter(Attendance.meeting_center_id == int(filter_meeting_center))

    # Obtener los registros de la tabla con los filtros aplicados
    records = query.all()

    # Crear una respuesta Flask con el contenido CSV
    def generate_csv():
        # Usar StringIO como buffer para escribir el CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Escribir los encabezados del archivo CSV
        headers = ['ID', 'Student Name', 'Class ID', 'Class Code', 'Sunday Date', 'Sunday Code', 'Submit Date', 'Meeting Center ID']
        writer.writerow(headers)

        # Escribir los datos de los registros
        for record in records:
            writer.writerow([
                record.id,
                record.student_name,
                record.class_id,
                record.class_code,
                record.sunday_date.strftime('%Y-%m-%d'),
                record.sunday_code,
                record.submit_date.strftime('%Y-%m-%d %H:%M:%S'),
                record.meeting_center_id
            ])

        # Mover el cursor al inicio del archivo en memoria para enviarlo como respuesta
        output.seek(0)
        return output.getvalue()

    # Crear la respuesta para el cliente
    return Response(
        generate_csv(),
        mimetype='text/csv',
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    ) 

# =============================================================================================
@bp.route('/attendance/monthly/<student_name>')
@login_required
def get_monthly_attendance(student_name):
    
    student_name = unquote(student_name)
    
    if not student_name:
        return jsonify({"error": "student_name is required"}), 400  # Retorna un error 400 en lugar de 404
    
    year              = request.args.get('year', type=int, default=2025)
    meeting_center_id = get_meeting_center_id()

    # Obtener la cantidad de asistencias por mes para el estudiante
    attendance_query = (
        db.session.query(func.strftime('%m', Attendance.sunday_date).label('month'),func.count().label('attendance_count'))
        .filter(Attendance.student_name == student_name)
        .filter(func.strftime('%Y', Attendance.sunday_date) == str(year))
        .filter(Attendance.meeting_center_id == meeting_center_id)
        .group_by(func.strftime('%m', Attendance.sunday_date))
        .all()
        )

    # Obtener el número total de semanas reportadas con asistencia por cada mes
    total_weeks_query = (
        db.session.query(func.strftime('%m', Attendance.sunday_date).label('month'),func.count(func.distinct(Attendance.sunday_date)).label('total_weeks'))
        .filter(func.strftime('%Y', Attendance.sunday_date) == str(year))
        .filter(Attendance.meeting_center_id == meeting_center_id)
        .group_by(func.strftime('%m', Attendance.sunday_date))
        .all()
        )

    # Convertir resultados en diccionarios
    attendance_dict  = {int(row.month): row.attendance_count for row in attendance_query}
    total_weeks_dict = {int(row.month): row.total_weeks for row in total_weeks_query}

    # Inicializar listas completas con 0s para los meses sin datos
    attendance_counts      = []
    attendance_percentages = []
    total_weeks_list       = []
    month_names            = []

    # Lista con todos los meses del año
    all_months        = list(range(1, 13))  # [1, 2, 3, ..., 12]
    months_translated = [_('Jan'), _('Feb'), _('Mar'), _('Apr'), _('May'), _('Jun'),
                    _('Jul'), _('Aug'), _('Sep'), _('Oct'), _('Nov'), _('Dec')]

    # Filtramos solo los meses con datos de asistencia o semanas reportadas
    for month in all_months:
        total_weeks      = total_weeks_dict.get(month, 0)
        attendance_count = attendance_dict.get(month, 0)
        percentage       = (attendance_count / total_weeks * 100) if total_weeks > 0 else 0

        # Solo agregar meses con datos de asistencia o semanas reportadas
        if attendance_count > 0 or total_weeks > 0:
            attendance_counts.append(attendance_count)
            attendance_percentages.append(round(percentage, 2))
            total_weeks_list.append(total_weeks)
            month_names.append(months_translated[month - 1])  # Guardar el nombre del mes correspondiente
    # Convertir números de meses en nombres
    
    month_names = [months_translated[m - 1] for m in all_months]
       
    # Lógica para obtener la frecuencia de clases por mes
    class_frequencies = {}
    for month in range(1, 13):
        class_frequencies[month] = {}

        attendances = Attendance.query.join(Classes).options(
            joinedload(Attendance.classes)
        ).filter(
            Attendance.student_name == student_name, extract('year', Attendance.sunday_date) == year, extract('month', Attendance.sunday_date) == month).with_entities(Classes.class_code).filter(Attendance.meeting_center_id == meeting_center_id).all()  # Recupera class_code

        for attendance in attendances:
            class_code = attendance[0]  # Extrae el valor de la tupla
            translated_code = _(class_code)  # Aplica la traducción en Python
            class_frequencies[month][translated_code] = class_frequencies[month].get(translated_code, 0) + 1

    return jsonify({
        "months": month_names,
        "attendance_percentages": attendance_percentages,
        "attendance_counts": attendance_counts,
        "total_weeks": total_weeks_list,
        "class_frequencies": class_frequencies
    })

    
# =============================================================================================
@bp.route('/registrar', methods=['POST'])
def registrar():
    usuario       = session.get('user_name')
    # 🔍 Depurar: Ver qué datos llegan al servidor
    print("Datos recibidos en el servidor:", request.form.to_dict())
    try:
        class_code   = request.form.get('classCode')
        sunday_date  = get_next_sunday()
        sunday_code  = request.form.get('sundayCode')
        unit_number  = request.form.get('unitNumber')
        student_name = request.form.get('studentName') 
               
        # Limpiar el nombre recibido
        student_name     = ' '.join(student_name.strip().split()) # Elimina espacios antes y después
        student_name     = student_name.title() # Convertir a título (primera letra en mayúscula) 
        student_name     = remove_accents(student_name) # Elimina los acentos
        nombre, apellido = student_name.split(" ", 1) # Dividir el nombre y apellido, asumiendo que solo hay un nombre y un apellido        
        formatted_name   = f"{apellido}, {nombre}" # Formatear el nombre como "apellido, nombre"

        # Verificar si la clase es válida
        class_entry = Classes.query.filter_by(class_code=class_code).first()
        print(f"Class Entry: {class_entry}") 
        if not class_entry:
            return jsonify({
                "success": False,
                "message": _('The selected class is not valid.'),
            }), 409

        # Verificar si el Meeting Center es válido
        meeting_center = MeetingCenter.query.filter_by(unit_number=unit_number).first()
        if not meeting_center:
            return jsonify({
                "success": False,
                "message": _('The church unit is invalid.'),
            }), 409
        
        correction = NameCorrections.query.filter_by(wrong_name=formatted_name, meeting_center_id=meeting_center.id).first()
        if correction:
            formatted_name = correction.correct_name

        # Obtener el estado del bypass desde la tabla Setup
        bypass_entry  = Setup.query.filter_by(key='allow_weekday_attendance').first()
        bypass_active = bypass_entry and bypass_entry.value.lower() == 'yes'

        # Si la clase es Main y hay restricciones de día
        if class_entry.class_type == "Main":
            # Si el bypass NO está activo o la unidad NO es la de prueba (ID = 2), aplicar restricciones
            if not (bypass_active and meeting_center.id == 2):
                if meeting_center.is_restricted:
                    grace_period_hours = int(meeting_center.grace_period_hours) if meeting_center.grace_period_hours else 0
                    time_now           = datetime.now()

                    start_time = meeting_center.start_time
                    end_time   = meeting_center.end_time

                    if isinstance(start_time, str):
                        start_time = datetime.strptime(start_time, "%H:%M").time()
                    if isinstance(end_time, str):
                        end_time   = datetime.strptime(end_time, "%H:%M").time()

                    today            = datetime.today()
                    start_time_dt    = datetime.combine(today, start_time)
                    end_time_dt      = datetime.combine(today, end_time)
                    grace_start_time = start_time_dt - timedelta(hours=grace_period_hours)
                    grace_end_time   = end_time_dt + timedelta(hours=grace_period_hours)

                    if not (grace_start_time <= time_now <= grace_end_time):
                        return jsonify({
                            "success": False,
                            "message": _('Attendance can only be recorded during the grace period or meeting time.'),
                        }), 403

                # Verificar si ya existe un registro en una clase `Main` ese domingo
                existing_main_attendance = Attendance.query.filter_by(
                    student_name      = formatted_name,
                    sunday_date       = sunday_date,
                    meeting_center_id = meeting_center.id,
                ).join(Classes).filter(Classes.class_type == "Main").first()

                if existing_main_attendance:
                    return jsonify({
                        "success": False,
                        "error_type": "main_class_restriction",
                        "message": _("%(name)s! You have already registered for a Sunday class today!") % {'name': formatted_name}
                    }), 409

        elif class_entry.class_type == "Extra":
            # Verificar si ya existe un registro para una clase `Extra` ese domingo
            existing_extra_attendance = Attendance.query.filter_by(
                student_name      = formatted_name,
                class_id          = class_entry.id,
                sunday_date       = sunday_date,
                meeting_center_id = meeting_center.id
            ).first()

            if existing_extra_attendance:
                return jsonify({
                    "success": False,
                    "message": _("%(name)s! You already have an attendance registered for this class on Sunday %(date)s!") % {
                        'name': formatted_name, 
                        'date': sunday_date.strftime('%b %d, %Y')
                    }
                }), 400
            
        created_by = nombre # Usa el nombre del estudiante para este campo
        if usuario:
            created_by = usuario # Si el usuario esta autenticado, se usa su nombre
        
        # Registrar la asistencia
        new_attendance = Attendance(
            student_name        = formatted_name,
            class_id            = class_entry.id,
            class_code          = class_code,
            sunday_date         = sunday_date,
            sunday_code         = sunday_code,
            meeting_center_id   = meeting_center.id,
            created_by          = created_by
        )
        db.session.add(new_attendance)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": _('Attendance recorded successfully.'),
            "student_name": student_name,
            "class_name": class_entry.class_name,
            "sunday_date": sunday_date.strftime("%b %d, %Y")
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": _('There was an error recording attendance: %(error)s') % {'error': str(e)}
        }), 500

       
# =============================================================================================
@bp.route('/pdf/list', methods=['GET'])
@login_required
def list_pdfs():
    meeting_center_id = get_meeting_center_id()
    OUTPUT_DIR = get_output_dir()
    
    # Verificar si hay clases asociadas al meeting center
    has_classes       = Classes.query.filter_by(meeting_center_id=meeting_center_id, is_active=True).first() is not None
    
    # Verificar si hay clases 'Main' o 'Extra' activas
    has_main_classes  = Classes.query.filter_by(meeting_center_id=meeting_center_id, is_active=True, class_type='Main').first() is not None

    has_extra_classes = Classes.query.filter_by(meeting_center_id=meeting_center_id, is_active=True, class_type='Extra').first() is not None
     
    if not os.path.exists(OUTPUT_DIR):
      os.makedirs(OUTPUT_DIR)  # Crea el directorio si no existe
      
    directory = os.path.join(os.getcwd(), OUTPUT_DIR)
    pdf_files = os.listdir(directory)
    
    return render_template('list_pdfs.html', pdf_files=pdf_files, has_classes=has_classes, has_main_classes=has_main_classes, has_extra_classes=has_extra_classes)


# =============================================================================================
@bp.route('/pdf/generate_all', methods=['GET', 'POST'])
@login_required
def generate_all_pdfs():
    return redirect(url_for('routes.generate_pdfs', type='todos'))  # redirige a la misma función con parámetro "todos"


# =============================================================================================
@bp.route('/pdf/generate_week', methods=['GET', 'POST'])
@role_required('Admin', 'Super', 'Owner')
def generate_week_pdfs():
    return redirect(url_for('routes.generate_pdfs', type='semana_especifica'))  # redirige a la misma función para PDFs de la semana específica


# =============================================================================================
@bp.route('/pdf/generate_extra', methods=['GET', 'POST'])
@login_required
def generate_extra_pdfs():
    selected_date = request.form.get('date')  # Obtener la fecha desde el formulario

    # Validar si la fecha fue proporcionada
    if not selected_date:
        flash(_('You must provide a date for this class.'), 'danger')
        return redirect(url_for('routes.list_classes'))

    # Redirigir a la función generate_pdfs con la fecha como argumento
    return redirect(url_for('routes.generate_pdfs', type='extra', selected_date=selected_date))


# =============================================================================================
@bp.route('/pdf/generate', methods=['GET', 'POST'])
@login_required
def generate_pdfs():
    user_date = request.args.get('selected_date')
    
    OUTPUT_DIR = get_output_dir()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    def get_class_date(class_type, user_date=None):
        if class_type == 'Main':
            return get_next_sunday()
        elif class_type == 'Extra' and user_date:
            try:
                class_date = datetime.strptime(user_date, '%Y-%m-%d')
                if class_date.date() >= datetime.today().date():
                    return class_date
                else:
                    raise ValueError(_('The date must be today or in the future.'))
            except ValueError as e:
                flash(str(e), 'error')
                return None
        else:
            flash(_('Invalid date for extra class.'), 'error')
            return None

    next_sunday_code  = get_next_sunday_code(get_next_sunday())
    meeting_center_id = session['meeting_center_id']
    unit_name         = session['meeting_center_name']
    unit              = session['meeting_center_number']
    sunday_week       = (get_next_sunday().day - 1) // 7 + 1

    clases_a_imprimir = list({
        c for c in (
            Classes.query.filter_by(is_active=True, meeting_center_id=meeting_center_id)
            if request.args.get('type') == 'todos'
            else Classes.query.filter_by(is_active=True, class_type='Extra', meeting_center_id=meeting_center_id)
            if request.args.get('type') == 'extra'
            else [
                c for c in Classes.query.filter_by(is_active=True, meeting_center_id=meeting_center_id)
                if str(sunday_week) in c.schedule.split(',')
            ]
        )
    })
    clean_qr_folder(OUTPUT_DIR)

    for class_entry in clases_a_imprimir:
        if class_entry.class_type == 'Extra' and not user_date:
            continue

        class_date = get_class_date(class_entry.class_type, user_date)
        if not class_date:
            continue

        class_name  = class_entry.translated_name
        class_code  = class_entry.class_code
        class_color = class_entry.class_color or "black"

        qr_url = f"{Config.BASE_URL}/attendance?className={class_name.replace(' ', '+')}&sundayCode={next_sunday_code}&date={class_date.strftime('%Y-%m-%d')}&unitNumber={unit}&classCode={class_code}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=class_color, back_color="white")

        qr_filename = os.path.join(OUTPUT_DIR, f"{class_name}_{format_date(class_date)}.png")
        img.save(qr_filename)

        pdf_filename = os.path.join(OUTPUT_DIR, f"{_(class_name)}_{format_date(class_date)}.pdf")
        c = canvas.Canvas(pdf_filename, pagesize=letter)

        page_width, page_height = letter
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor("black")
        c.drawCentredString(page_width / 2, 600, _(f"Attendance Sheet"))
        
        rec_x=45
        rec_y=45
        c.rect(rec_x+22, rec_y, (page_width-rec_x * 2)-44, page_height - rec_y * 4)
        
        qr_image = ImageReader(qr_filename)
        qr_size = 442
        qr_x=85
        qr_y=115
        c.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)

        c.setFont("Helvetica-Bold", 35)
        c.drawCentredString(page_width / 2, 560, _(class_name))
        
        c.setFont("Helvetica", 16)
        c.drawCentredString(page_width / 2, 99, unit_name)
        c.drawCentredString(page_width / 2, 74, f"{format_date(class_date)}") 

        c.setLineWidth(0.5)
        c.setDash(5, 10)
        c.line(0, page_height - rec_y * 4 +68, 612, page_height - rec_y * 4 +68)
        c.line(rec_x, 0, rec_x, page_height)
        c.line(567, 0, 567, page_height)
        c.line(0, 22.5, page_width, 22.5)
        c.showPage()
           
        # Segunda página con QR de reset y QR del maestro si ya existe
        # QR para resetear el nombre
        manual_qr_url = f"{Config.BASE_URL}/attendance/manual"
        manual_qr = qrcode.QRCode(version=1, box_size=5, border=2)
        manual_qr.add_data(manual_qr_url)
        manual_qr.make(fit=True)
        manual_img = manual_qr.make_image(fill_color="black", back_color="white")
        manual_qr_filename = os.path.join(OUTPUT_DIR, "manual_attendance.png")
        manual_img.save(manual_qr_filename)

        reset_qr_image = ImageReader(manual_qr_filename)
        c.drawCentredString(page_width / 2, 605, _('Register Manual Attendance'))
        c.drawImage(reset_qr_image, page_width / 2 - 50, 500, width=100, height=100)

        # Verificar si el QR del maestro ya existe
        classes_teacher = {
            "YW": "RS",
            "AP": "EQ",
            "SSY": "SSA"
        }        
        # Obtener el nombre de la clase del maestro usando el código del maestro
        class_teacher = classes_teacher.get(class_code)
        if class_teacher:
            # Buscar la clase asociada al código del maestro
            teacher_class = Classes.query.filter_by(class_code=class_teacher).first()
            
            if teacher_class:
                teacher_class_name = teacher_class.translated_name  # Obtén el nombre de la clase

                # Crear el nombre del archivo para el QR del maestro
                teacher_qr_filename = os.path.join(OUTPUT_DIR, f"{class_teacher}_{format_date(class_date)}.png")

                # Comprobar si el QR del maestro ya existe
                if os.path.exists(teacher_qr_filename):  # Si el QR ya existe, reutilízalo
                    teacher_qr_image = ImageReader(teacher_qr_filename)
                else:  # Si no existe, genera uno nuevo
                    teacher_qr_url = f"{Config.BASE_URL}/attendance?className={teacher_class_name.replace(' ', '+')}&classCode={class_teacher}&date={class_date.strftime('%Y-%m-%d')}&sundayCode={next_sunday_code}&unitNumber={unit}"
                    teacher_qr = qrcode.QRCode(version=1, box_size=10, border=4)
                    teacher_qr.add_data(teacher_qr_url)
                    teacher_qr.make(fit=True)
                    teacher_img = teacher_qr.make_image(fill_color="black", back_color="white")
                    teacher_img.save(teacher_qr_filename)
                    teacher_qr_image = ImageReader(teacher_qr_filename)

                # Dibujar el QR del maestro en la página
                teacher_qr_size = 180
                teacher_qr_x = (page_width - teacher_qr_size) / 2
                teacher_qr_y = 90
                c.drawImage(teacher_qr_image, teacher_qr_x, teacher_qr_y, width=teacher_qr_size, height=teacher_qr_size)
                c.drawCentredString(page_width / 2, teacher_qr_y + teacher_qr_size, _('Teacher\'s Attendance Class'))  # Mostrar el nombre de la clase del maestro
                c.setFont("Helvetica-Bold", 14)
                c.drawCentredString(page_width / 2, teacher_qr_y - 10, teacher_class_name)  # Mostrar el nombre de la clase del maestro

        # Guardar la página PDF
        c.save()

    clean_qr_images(OUTPUT_DIR)
    flash(_('QR Codes generated successfully.'), 'success')
    return redirect(url_for('routes.list_pdfs'))


# =============================================================================================
@bp.route('/pdf/view/<path:filename>', methods=['GET'])
@login_required
def view_pdf(filename):
    OUTPUT_DIR = get_output_dir()
    try:
        directory = os.path.join(os.getcwd(), OUTPUT_DIR)
        filename = unquote(filename)
        full_path = os.path.join(directory, filename)

        print(f"Trying to access: {full_path}")  # Debugging output

        if not os.path.exists(full_path):
            print("File not found:", full_path)  # More detailed log
            abort(404, description=f"File not found: {filename}")

        return send_from_directory(directory, filename, as_attachment=False)  # Se muestra en el navegador
    except Exception as e:
        print(f"Error: {e}")  # Log the actual error for debugging
        abort(500, description=str(e))
        
        
# =============================================================================================
# CRUD para Meeting Centers
@bp.route('/meeting_centers/', methods=['GET', 'POST'])
@role_required('Owner')
def meeting_centers():
    meeting_centers    = MeetingCenter.query.all()
    main_classes_exist = {mc.id: Classes.query.filter_by(meeting_center_id=mc.id, class_type='Main').count() > 0 for mc in meeting_centers}
    return render_template('meeting_centers.html', meeting_centers=meeting_centers, main_classes_exist=main_classes_exist)


# =============================================================================================
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
        flash(_('Meeting center created successfully!'), 'success')
        return redirect(url_for('routes.meeting_centers'))
    return render_template('form.html', form=form, title=_('Create new Meeting center'), submit_button_text=_('Create'), clas='warning')


# =============================================================================================
@bp.route('/meeting_center/edit/<int:id>', methods=['GET', 'POST'])
@role_required('Owner')
def update_meeting_center(id):
    meeting_center = MeetingCenter.query.get_or_404(id)
    form           = MeetingCenterForm(obj=meeting_center)
    if form.validate_on_submit():
        form.populate_obj(meeting_center)
        db.session.commit()
        flash(_('Meeting Center updated successfully.'), 'success')
        return redirect(url_for('routes.meeting_centers'))
    return render_template('form.html', form=form, title=_('Edit Meeting Center'), submit_button_text=_('Update'), clas='warning')


# =============================================================================================
@bp.route('/meeting_center/delete/<int:id>', methods=['POST'])
@role_required('Owner')
def delete_meeting_center(id):
    meeting_center = MeetingCenter.query.get_or_404(id)
    if meeting_center.attendances:
        flash(_('The meeting center cannot be deleted because it has registered attendance.'), 'danger')
        return redirect(url_for('routes.meeting_centers'))
    
    db.session.delete(meeting_center)
    db.session.commit()
    flash(_('Meeting Center successfully removed.'), 'success')
    return redirect(url_for('routes.meeting_centers'))


# =============================================================================================
@bp.route('/meeting_center/set', methods=['POST'])
@login_required
def set_meeting_center():
    data = request.get_json()
    meeting_center_id = data.get('meeting_center_id', 'all')

    session['meeting_center_id'] = meeting_center_id

    # Si el usuario seleccionó "all", no hay un centro de reuniones específico
    if meeting_center_id == 'all':
        session['meeting_center_name']   = _('All Meeting Centers')
        session['meeting_center_number'] = 'N/A'  # Establecer el número como N/A
    else:
        # Buscar el centro de reuniones en la base de datos
        meeting_center = MeetingCenter.query.get(meeting_center_id)
        if meeting_center:
            session['meeting_center_name']   = meeting_center.name
            session['meeting_center_number'] = meeting_center.unit_number  # Obtener el número del centro de reuniones
        else:
            session['meeting_center_name']   = _('Unknown')
            session['meeting_center_number'] = 'N/A'  # En caso de error, asignar N/A

    return jsonify({
        "meeting_center_id"    : session['meeting_center_id'],
        "meeting_center_name"  : session['meeting_center_name'],
        "meeting_center_number": session['meeting_center_number']  # Enviar el número también
    })

    
# =============================================================================================
@bp.route('/meeting_center/api')
@login_required
def get_meeting_centers():
    meeting_centers = MeetingCenter.query.order_by(MeetingCenter.name).all()
    return jsonify([{"id": mc.id, "name": mc.name} for mc in meeting_centers])


# =============================================================================================
@bp.route('/classes', methods=['GET'])
@role_required('Admin', 'Super', 'Owner')
def classes():
    # Obtener rol, organization_id y meeting_center_id de la sesión
    role = session.get('role')
    organization_id = session['organization_id']
    meeting_center_id = get_meeting_center_id()
    
    # Inicializar la consulta básica
    query = db.session.query(
        Classes.id,
        Classes.class_name,
        Classes.short_name,
        Classes.class_code,
        Classes.class_type,
        Classes.schedule,
        Classes.is_active,
        Classes.class_color,
        Classes.organization_id,
        MeetingCenter.short_name.label('meeting_short_name')
    ).join(MeetingCenter, Classes.meeting_center_id == MeetingCenter.id)

    # Verificar si el rol es Admin
    if role == 'Admin': # Si es Admin, filtrar por meeting_center_id        
        query = query.filter(Classes.meeting_center_id == meeting_center_id)
    elif role == 'Super':# Si es Super, filtrar por organization_id y meeting_center_id       
        query = query.filter(Classes.organization_id == organization_id)
        query = query.filter(Classes.meeting_center_id == meeting_center_id)   
    elif role == 'Owner': # Si no es Admin ni Super, aplicar la lógica existente para Owner
        if not (meeting_center_id == 'all'):
            query = query.filter(Classes.meeting_center_id == meeting_center_id)
    
    # Ejecutar la consulta
    classes = query.all()

    return render_template('classes.html', classes=classes)


# =============================================================================================
@bp.route('/class/new', methods=['GET', 'POST'])
@role_required('Admin', 'Super', 'Owner')
def create_class():
    # Obtener rol, organization_id y meeting_center_id de la sesión
    meeting_center_id = get_meeting_center_id()
    organization_id   = session['organization_id']
    role              = session.get('role')
    form              = ClassForm()

    if role == 'Owner':
        form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]
    else:
        form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.filter_by(id=meeting_center_id).all()]

    if (role == 'Owner' or role == 'Admin'):
        form.organization_id.choices = [(og.id, og.name) for og in Organization.query.all()]
    else:
        form.organization_id.choices = [(og.id, og.name) for og in Organization.query.filter_by(id=organization_id).all()]
    
    if form.validate_on_submit():
        new_class = Classes(
            class_name          = form.class_name.data,
            short_name          = form.short_name.data,
            class_code          = form.class_code.data,
            class_type          = form.class_type.data,
            schedule            = form.schedule.data,
            is_active           = form.is_active.data,
            class_color         = form.class_color.data,
            meeting_center_id   = form.meeting_center_id.data,
            organization_id     = form.organization_id.data
        )
        try:
            db.session.add(new_class)
            db.session.commit()
            flash(_('Class created successfully!'), 'success')
            return redirect(url_for('routes.classes'))
        except IntegrityError:
            db.session.rollback()
            flash(_('A class with this name, short name, or code already exists in the same church unit.'), 'danger')
    return render_template('form.html', form=form, title=_('Create new Class'), submit_button_text=_('Create'), clas='warning')


# =============================================================================================
@bp.route('/class/edit/<int:id>', methods=['GET', 'POST'])
@role_required('Admin', 'Super', 'Owner')
def update_class(id):
    class_instance = Classes.query.get_or_404(id)
    form           = ClassForm(obj=class_instance)
    form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]
    form.organization_id.choices = [(og.id, og.name) for og in Organization.query.all()]
    
    if form.validate_on_submit():
        class_instance.class_name        = form.class_name.data
        class_instance.short_name        = form.short_name.data
        class_instance.class_code        = form.class_code.data
        class_instance.class_type        = form.class_type.data
        class_instance.schedule          = form.schedule.data
        class_instance.is_active         = form.is_active.data
        class_instance.class_color       = form.class_color.data
        class_instance.meeting_center_id = form.meeting_center_id.data
        class_instance.organization_id   = form.organization_id.data
        try:
            db.session.commit()
            flash(_('Class updated successfully!'), 'success')
            return redirect(url_for('routes.classes'))
        except IntegrityError:
            db.session.rollback()
            flash(_('A class with this name, short name, or code already exists in the same church unit.'), 'danger')
    return render_template('form.html', form=form, title=_('Edit Class'), submit_button_text=_('Update'), clas='warning', backroute='classes')


# =============================================================================================
@bp.route('/class/reset_color/<int:class_id>', methods=['POST'])
@login_required
def reset_class_color(class_id):
    class_obj = Classes.query.get_or_404(class_id)
    try:
        class_obj.class_color = "#000000"
        db.session.commit()
        return jsonify({"message": "Color restablecido con éxito."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al restablecer el color: {str(e)}"}), 500

# =============================================================================================
@bp.route('/class/delete/<int:id>', methods=['POST'])
@role_required('Admin', 'Owner')
def delete_class(id):
    class_instance = Classes.query.get_or_404(id)
    if class_instance.attendances:
        flash(_('The class cannot be deleted because it has attendance recorded.'), 'danger')
        return redirect(url_for('routes.classes'))
    if class_instance.class_type == 'main':
        flash(_('Cannot delete a main class.'), 'warning')
        return redirect(url_for('routes.classes'))
    try:
        db.session.delete(class_instance)
        db.session.commit()
        flash(_('Class deleted successfully!'), 'success')
    except Exception as e:
        db.session.rollback()
        flash(_('Error deleting class: %(error)s') % {'error': e}, 'danger')
        
    return redirect(url_for('routes.classes'))


# =============================================================================================
@bp.route('/organizations', methods=['GET'])
@role_required('Owner')
def organizations():
    organizations = Organization.query.all()
    return render_template('organizations.html', organizations=organizations)


# =============================================================================================
@bp.route('/organizations/new', methods=['GET', 'POST'])
@role_required('Owner')
def create_organization():
    form = OrganizationForm()
    if form.validate_on_submit():
        new_org = Organization(name=form.name.data)
        try:
            db.session.add(new_org)
            db.session.commit()
            flash(_('Organization created successfully!'), 'success')
            return redirect(url_for('routes.organizations'))
        except Exception as e:
            db.session.rollback()
            flash(_('Error: Organization name must be unique.'), 'danger')
            return redirect(url_for('routes.organizations'))
    return render_template('form.html', form=form, title=_('Create new Organization'), submit_button_text=_('Create'), clas='warning')


# =============================================================================================
@bp.route('/organizations/edit/<int:id>', methods=['GET', 'POST'])
@role_required('Owner')
def edit_organization(id):
    organization = Organization.query.get_or_404(id)
    form         = OrganizationForm(obj=organization)
    if form.validate_on_submit():
        organization.name = form.name.data
        try:
            db.session.commit()
            flash(_('Organization updated successfully!'), 'success')
            return redirect(url_for('routes.organizations'))
        except Exception as e:
            db.session.rollback()
            flash(_('Error: Organization name must be unique.'), 'danger')
    return render_template('form.html', form=form, title=_('Edit Organization'), submit_button_text=_('Update'), clas='warning', organization=organization)


# =============================================================================================
@bp.route('/organizations/delete/<int:id>', methods=['POST'])
@role_required('Owner')
def delete_organization(id):
    organization = Organization.query.get_or_404(id)
    try:
        db.session.delete(organization)
        db.session.commit()
        flash(_('Organization deleted successfully!'), 'success')
    except Exception as e:
        db.session.rollback()
        flash(_('Error: Could not delete organization.'), 'danger')
    return redirect(url_for('routes.organizations'))


# =============================================================================================
@bp.route('/get_swal_texts', methods=['GET'])
def get_swal_texts():
    return {    
        'actionCanceled'          : _("Action canceled"),
        'alreadyRegistered'       : _("You already have registered assistance on {sunday_date}."),
        'atention'                : _("Attention"),
        'attendance_label'        : _("Attendance"),
        'attendance_unit'         : _("attendance(s)"),
        'attendance_value_label'  : _("Attendance"),
        'attendanceRecorded'      : _("¡{student_name}, your attendance was recorded!"),
        'cancel'                  : _("Cancel"),
        'cancelled'               : _("Cancelled"),
        'cancelledMessage'        : _("No correction has been made."),
        'chooseClass'             : _("Choose a Class"),
        'classesLabel'            : _("Classes"),
        'classesNumber'           : _("Number of Classes"),
        'classesTitle'            : _("Frequency of Classes per Month"),
        'cleared'                 : _("Cleared!"),
        'colorErrorText'          : _("There was a problem resetting the color."),
        'colorResetText'          : _("This will reset the class color to black."),
        'colorSuccessText'        : _("The color has been successfully restored."),
        'confirm'                 : _("Confirm"),
        'confirmDelete'           : _("You \'re sure?"),
        'confirmRegisterCancel'   : _("No, cancel!"),
        'confirmRegisterText'     : _("Do you want to register attendance for the selected students?"),
        'confirmRegisterTitle'    : _("Confirm Attendance Registration"),
        'confirmRegisterYes'      : _("Yes, register it!"),
        'confirmRegSuccessText'   : _("Attendance has been registered successfully."),
        'confirmRegSuccessTitle'  : _("Success"),
        'confirmSave'             : _("Confirm"),
        'connectionError'         : _("There was a problem connecting to the server."),
        'deleteConfirmationText'  : _("This action will delete all records and cannot be undone."),
        'deleteOneRecordText   '  : _("This record will be deleted."),
        'errorMessage'            : _("There was a problem saving the correction"),
        'errorTitle'              : _("Error"),
        'great'                   : _("Great!"),
        'incorrectPatternLabel'   : _("Incorrect format"),
        'incorrectPatternText'    : _("The name must be in the format 'Last Name, First Name', separated by a comma."),
        'members_label'           : _("members"),
        'monthly_attendance'      : _("Monthly Attendance"),
        'monthlyAttendancePerc'   : _("Monthly Attendance Percentage"),
        'months_label'            : _("Months"),
        'mustSelectDate'          : _("You must select a date!"),
        'nameFormatText'          : _("Please enter your name in \'First Name Last Name\' format."),
        'nameNotRemoved'          : _("Your name was not removed."),
        'nameRemoved'             : _("The name has been removed."),
        'noNameFound'             : _("No Name Found"),
        'noNameSaved'             : _("No name is currently saved."),
        'noQrGenerated'           : _("QR codes were not generated"),
        'promotionConfirmation'   : _("Yes, Do it!"),
        'promotionText'           : _("Do you want to promote \'{user_name}\' as a Power User?"),
        'promotionTitle'          : _("You 're sure?"),
        'registrationCancel'      : _("Attendance registration cancelled."),
        'registrationError'       : _("There was an error registering attendance."),
        'resetStudentName'        : _("Reset Student Name"),
        'revertConfirmButton'     : _("Revert"),
        'revertTitle'             : _("Are you sure you want to revert this correction?"),
        'savedNameText'           : _("The saved name is: \'{name}\'. Do you want to clear it?"),
        'selectDateExtraClasses'  : _("Select a date for Extra classes"),
        'successMessage'          : _("The name has been corrected"),
        'successTitle'            : _("¡Success"),
        'sundayClassRestriction'  : _("You cannot register a \'Sunday Class\' outside of Sunday."),
        'validationError'         : _("Error, There was a problem validating the attendance."),
        'warningTitle'            : _("warning"),
        'weeks_label'             : _("Weeks with attendance"),       
        'wrongNameLabel'          : _("Correct Format: Last Name, First Name"),
        'wrongNamePlaceholder'    : _("Enter the new name"),
        'wrongNameText'           : _("Please enter the correct name for "),
        'wrongNameTitle'          : _("Please enter the correct name"),
        'yes'                     : _("Yes"),
        'yesClearIt'              : _("Yes, clear it!"),
        'yesDeleteEverything'     : _("Yes, delete everything"),
        'yesDeleteIt'             : _("Yes, Delete it!"),
        'yesResetIt'              : _("Yes, Reset it!"),
    }
    
    
# =============================================================================================   
@bp.route('/classes/populate/<int:id>', methods=['GET', 'POST'])
@role_required('Owner')
def populate_classes(id):
    new_meeting_center_id = id

    # Arreglo estático con las clases tipo Main
    main_classes_static = [
        {
            'class_name'     : _('Elders Quorum'),
            'short_name'     : _('Elders_Q'),
            'class_code'     : _('EQ'),
            'class_type'     : _('Main'),
            'schedule'       : '2,4',
            'is_active'      : True,
            'class_color'    : None,
            'organization_id': 2
        },
        {
            'class_name'     : _('Aaronic Priesthood'),
            'short_name'     : _('Aaronic_P'),
            'class_code'     : _('AP'),
            'class_type'     : _('Main'),
            'schedule'       : '2,4',
            'is_active'      : True,
            'class_color'    : None,
            'organization_id': 4
        },
        {
            'class_name'     : _('Relief Society'),
            'short_name'     : _('Relief_S'),
            'class_code'     : _('RS'),
            'class_type'     : _('Main'),
            'schedule'       : '2,4',
            'is_active'      : True,
            'class_color'    : '#ba8e23',
            'organization_id': 3
        },
        {
            'class_name'     : _('Young Woman'),
            'short_name'     : _('Young_W'),
            'class_code'     : _('YW'),
            'class_type'     : _('Main'),
            'schedule'       : '2,4',
            'is_active'      : True,
            'class_color'    : '#943f88',
            'organization_id': 5
        },
        {
            'class_name'     : _('Sunday School Adults'),
            'short_name'     : _('S_S_Adults'),
            'class_code'     : _('SSA'),
            'class_type'     : _('Main'),
            'schedule'       : '1,3',
            'is_active'      : True,
            'class_color'    : None,
            'organization_id': 6
        },
        {
            'class_name'     : _('Sunday School Youth'),
            'short_name'     : _('S_S_Youth'),
            'class_code'     : _('SSY'),
            'class_type'     : _('Main'),
            'schedule'       : '1,3',
            'is_active'      : True,
            'class_color'    : None,
            'organization_id': 6
        },
        {
            'class_name'     : _('Fifth Sunday'),
            'short_name'     : _('F_Sunday'),
            'class_code'     : _('FS'),
            'class_type'     : _('Main'),
            'schedule'       : '5',
            'is_active'      : True,
            'class_color'    : None,
            'organization_id': 1
        }
    ]
    try:
        # Validar si ya existen clases asociadas al nuevo Meeting Center
        existing_classes = Classes.query.filter_by(meeting_center_id=new_meeting_center_id).first()
        if existing_classes:
            flash(_('Classes already exist for this meeting center'), 'warning')
            return redirect(url_for('routes.meeting_centers'))

        # Insertar las clases del arreglo estático
        for class_data in main_classes_static:
            new_class = Classes(
                class_code        = class_data['class_code'],
                class_color       = class_data['class_color'],
                class_name        = class_data['class_name'],
                class_type        = class_data['class_type'],
                is_active         = class_data['is_active'],
                meeting_center_id = new_meeting_center_id,
                organization_id   = class_data['organization_id'],
                schedule          = class_data['schedule'],
                short_name        = class_data['short_name'],
            )
            db.session.add(new_class)

        # Confirmar los cambios en la base de datos
        db.session.commit()
        flash(_('Main classes successfully populated.'), 'success')

    except IntegrityError as ie:
        db.session.rollback()

        flash(_('Unique constraint error:  %(error)s') % {'error':str(ie)}, 'danger')
    except Exception as e:
        db.session.rollback()
        flash(_('Error duplicating main classes for new meeting center: %(error)s') % {'error':str(ie)}, 'danger')

    return redirect(url_for('routes.meeting_centers'))


# =============================================================================================
@bp.route('/update_name_correction', methods=['POST'])
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
  
    
# =============================================================================================       
@bp.route('/admin', methods=['GET', 'POST'])
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

        return redirect(url_for('routes.admin', meeting_center_id=meeting_center_id))
    
    verification_enabled = code_verification_setting.value if code_verification_setting else 'true'

    return render_template('admin.html', 
                           verification_enabled = verification_enabled,
                           bypass_enabled       = bypass_enabled,
                           name_corrections     = name_corrections,
                           meeting_center_id    = meeting_center_id)


# ============================================================================================= 
@bp.route('/admin/get_settings', methods=['GET'])
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
@bp.route('/admin/bypass', methods=['POST'])
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
    return redirect(url_for('routes.admin', bypass_enabled=new_value))


# =============================================================================================
@bp.route('/admin/name_correction/delete/<int:id>', methods=['POST'])
@login_required
def delete_name_correction(id):
    correction = NameCorrections.query.get_or_404(id)  # Buscar el registro por ID
    db.session.delete(correction)  # Eliminar el registro
    db.session.commit()  # Guardar los cambios
    flash(_('Name correction deleted successfully!'), "success")
    return redirect(url_for('routes.admin'))  # Redirigir a la vista admin


# =============================================================================================
@bp.route('/admin/name_correction/revert/<int:id>', methods=['POST'])
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
    return redirect(url_for('routes.admin'))


# =============================================================================================
@bp.route('/admin/name_corrections/filter', methods=['GET'])
@login_required
def filter_name_corrections():
    meeting_center_id = request.args.get('meeting_center_id', type=int)
    
    if meeting_center_id == 'all' or meeting_center_id is None:
        name_corrections = NameCorrections.query.all()
    else:
        name_corrections = NameCorrections.query.filter_by(meeting_center_id=meeting_center_id).all()
    
    return render_template('partials/tables/name_correction_table.html', name_corrections=name_corrections)


# =============================================================================================
@bp.route('/api/admin_data')
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


# =============================================================================================
@bp.route('/stats')
@role_required('Owner', 'Admin')
def render_stats():

    meeting_center_id = get_meeting_center_id()
    current_year      = (datetime.now()).year
    year              = request.args.get('year', type=int, default=current_year)

    # Consultar años y meses disponibles
    year_query  = db.session.query(func.extract('year', Attendance.sunday_date)).distinct().order_by(func.extract('year', Attendance.sunday_date))
    month_query = db.session.query(func.extract('month', Attendance.sunday_date)).distinct().order_by(func.extract('month', Attendance.sunday_date))
    
    # Obtener clases disponibles
    class_query = db.session.query(Classes).filter(Classes.is_active == True)

    if meeting_center_id == 'all':
        meeting_center_id = None  # No aplicar filtro
    if meeting_center_id is not None:
        class_query = class_query.filter(Classes.meeting_center_id == meeting_center_id)
        year_query = year_query.filter(Attendance.meeting_center_id == meeting_center_id)
        month_query = month_query.filter(Attendance.meeting_center_id == meeting_center_id)

    # Datos disponibles para clases, años y meses
    available_classes = class_query.order_by(Classes.class_name).all()    
    available_years   = [y[0] for y in year_query.all() if y[0] is not None]
    available_months  = [m[0] for m in month_query.all() if m[0] is not None]
    month_names       = [{"num": m, "name": _(datetime(2000, m, 1).strftime('%b'))} for m in available_months]

    # Consultar los estudiantes con mejor asistencia
    students = (db.session.query(Attendance.student_name)
                .filter(Attendance.meeting_center_id == meeting_center_id)
                .distinct()
                .order_by(Attendance.student_name)
                .all())

    # Consultar los años disponibles para la asistencia
    years = (db.session.query(func.strftime('%Y', Attendance.sunday_date).label("year"))
             .filter(Attendance.meeting_center_id == meeting_center_id)
             .distinct()
             .order_by(func.strftime('%Y', Attendance.sunday_date).desc())
             .all())

    # Consultar los estudiantes con mejor asistencia
    student_attendance = (
        db.session.query(
            Attendance.student_name, func.count().label('attendance_count')
        )
        .filter(Attendance.meeting_center_id == meeting_center_id)
        .filter(func.strftime('%Y', Attendance.sunday_date) == str(year))
        .group_by(Attendance.student_name)
        .order_by(func.count().desc())  # Ordenado de mayor a menor
        .all()
    )
    # Procesar la lista de estudiantes con mejor y peor asistencia
    if not student_attendance:
        top_students = []
        bottom_students = []
    else:
        max_count = student_attendance[0][1]
        min_count = student_attendance[-1][1]

        # Obtener los mejores estudiantes
        top_attendance = []
        for student in student_attendance:
            if len(top_attendance) >= 10 and student[1] < max_count:
                break
            top_attendance.append(student)

        # Filtrar los estudiantes para los peores
        top_names = {student[0] for student in top_attendance}
        bottom_attendance = []
        for student in reversed(student_attendance):
            if len(bottom_attendance) >= 10 and student[1] > min_count:
                break
            if student[0] not in top_names:
                bottom_attendance.append(student)

        # Calcular el porcentaje de asistencia
        if max_count == min_count:
            top_students = [{"name": student[0], "attendance_percentage": 100} for student in top_attendance]
            bottom_students = [{"name": student[0], "attendance_percentage": 100} for student in bottom_attendance]
        else:
            top_students = [
                {"name": student[0], "attendance_percentage": round((student[1] / max_count) * 100)}
                for student in top_attendance
            ]
            bottom_students = sorted(
                [
                    {"name": student[0], "attendance_percentage": round((student[1] / max_count) * 100)}
                    for student in bottom_attendance
                ],
                key=lambda x: x["name"],  # Ordenar por nombre
                reverse=False  # Ascendente
            )

    # Convertir los resultados de estudiantes y años
    student_names = [student[0] for student in students]
    years         = [year[0] for year in years]

    # Retornar la plantilla con todos los datos
    return render_template('stats.html',
                           available_years   = available_years ,
                           available_months  = month_names ,
                           available_classes = available_classes ,
                           students          = student_names ,
                           years             = years ,
                           meeting_center_id = meeting_center_id ,
                           top_students      = top_students ,
                           disable_year      = len(available_years) == 1,
                           bottom_students   = bottom_students ,
                           current_year      = current_year)


# =============================================================================================
@bp.route("/classes_stats/data")
@role_required('Owner', 'Admin')
def get_classes_stats():
    """Devuelve los datos de asistencia filtrados para la gráfica."""
    meeting_center_id = get_meeting_center_id()
    if meeting_center_id == 'all':
        meeting_center_id = None  # No aplicar filtro

    current_year = (datetime.now()).year

    class_code     = request.args.get("class_code", type=str, default='all')
    selected_year  = request.args.get('year', type=int, default=current_year)
    selected_month = 'all'

    # Lista de todos los meses y nombres traducidos
    all_months        = list(range(1, 13))
    months_translated = [_('Jan'), _('Feb'), _('Mar'), _('Apr'), _('May'), _('Jun'),
                         _('Jul'), _('Aug'), _('Sep'), _('Oct'), _('Nov'), _('Dec')]

    # Construcción de la consulta base
    query = db.session.query(
        func.extract('month', Attendance.sunday_date).label("month"),
        func.count(func.distinct(Attendance.student_name)).label("count")
    ).group_by(func.extract('month', Attendance.sunday_date))

    if meeting_center_id is not None:
        query = query.filter(Attendance.meeting_center_id == meeting_center_id)

    # Filtrar por código de clase si se especifica
    if class_code and class_code != "all":
        query = query.filter(Attendance.class_code == class_code)

    # Filtrar por año si se especifica
    if selected_year:
        query = query.filter(func.extract("year", Attendance.sunday_date) == selected_year)

    # Filtrar por mes o trimestre
    month_filter = []
    if selected_month == "all":
        month_filter = all_months  # Todos los meses
    elif selected_month.startswith("Q"):
        quarter_map  = {"Q1": [1, 2, 3], "Q2": [4, 5, 6], "Q3": [7, 8, 9], "Q4": [10, 11, 12]}
        month_filter = quarter_map.get(selected_month, [])
    else:
        month_filter = [int(selected_month)]  # Mes específico

    if selected_month and selected_month != "all":
        query = query.filter(func.extract('month', Attendance.sunday_date).in_(month_filter))

    # Obtener resultados de asistencia
    results = query.all()

    # Inicializar diccionario con todos los meses en 0
    attendance_by_month = {m: 0 for m in all_months}

    # Rellenar con los datos reales obtenidos de la consulta
    for row in results:
        attendance_by_month[int(row.month)] = row.count

    # Convertir a lista de diccionarios para la respuesta JSON
    chart_data = [
        {"month": months_translated[m - 1], "value": attendance_by_month[m]}
        for m in all_months
    ]

    return jsonify({
        "chart_data": chart_data       
    })


# =============================================================================================
@bp.route("/attendance/check", methods=['POST', 'GET'])
@login_required
def register_attendance():
    meeting_center_id = get_meeting_center_id()
    sunday_date_str   = get_last_sunday()  # Retorna una cadena, e.g. "2025-02-09"
    sunday_date       = datetime.strptime(sunday_date_str, "%Y-%m-%d").date()
    sunday_week       = (get_next_sunday().day - 1) // 7 + 1
    role              = session.get('role')
    organization_id   = session.get('organization_id')

    print(f"Organization id: {organization_id}")

    time_range = request.args.get('time_range', 'last_two_weeks')

    if time_range == 'last_two_weeks':
        start_date = sunday_date - timedelta(weeks=2)
    elif time_range == 'last_month':
        start_date = sunday_date - timedelta(days=30)  # Aproximado a 30 días
    elif time_range == 'year_to_date':
        start_date = datetime(sunday_date.year, 1, 1)
    else:
        # Valor por defecto: últimas dos semanas
        start_date = sunday_date - timedelta(weeks=2)

    # Obtener clases activas filtradas por meeting_center_id
    class_query = db.session.query(Classes).filter(Classes.is_active == True)
    if meeting_center_id is not None:
        class_query = class_query.filter(Classes.meeting_center_id == meeting_center_id)
   
    if (role == 'Owner' or role == 'Operator' or organization_id == 1):
        available_classes = class_query.order_by(Classes.class_name).all()
    elif role == 'Admin':
         available_classes = list({
            c for c in Classes.query.filter_by(is_active=True, meeting_center_id=meeting_center_id)
                    if str(sunday_week) in c.schedule.split(',')
        })
    else:
        available_classes = list({
            c for c in Classes.query.filter_by(is_active=True, meeting_center_id=meeting_center_id, organization_id=organization_id)
                    if str(sunday_week) in c.schedule.split(',')
        })

    if request.method == 'POST':
        data = request.get_json()
        #print(f"Received data: {data}")

        student_names = data.get("student_names", [])
        class_code = data.get("class_code")

        # Buscar la clase usando class_code y meeting_center_id
        cls = Classes.query.filter_by(class_code=class_code, meeting_center_id=meeting_center_id).first()
        if not cls:
            return jsonify({"error": "Class not found."}), 404

        # Registrar asistencia si no existe
        for student_name in student_names:
            existing = Attendance.query.filter_by(
                student_name=student_name,
                class_id=cls.id,
                sunday_date=sunday_date,
                meeting_center_id=meeting_center_id
            ).first()
            if not existing:
                new_attendance = Attendance(
                    student_name=student_name,
                    class_id=cls.id,
                    class_code=class_code,
                    sunday_date=sunday_date,  # Objeto date
                    sunday_code=1111,
                    meeting_center_id=meeting_center_id,
                    submit_date=datetime.now(),
                )
                db.session.add(new_attendance)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
        
        # Obtener los registros de asistencia para la clase seleccionada, en el meeting_center y fecha indicados
        attendance_members = (
            db.session.query(Attendance.student_name)
            .filter(
                Attendance.meeting_center_id == meeting_center_id,
                Attendance.class_code == class_code,
                Attendance.sunday_date == sunday_date
            )
            .distinct()
            .order_by(Attendance.student_name)
            .all()
        )

        expected_student_names = (
            db.session.query(Attendance.student_name)
            .filter(
                Attendance.meeting_center_id == meeting_center_id,
                Attendance.class_code == class_code,
                Attendance.sunday_date >= start_date,  # Filtramos por el rango de tiempo
                ~Attendance.student_name.in_(
                    db.session.query(Attendance.student_name)
                    .filter(
                        Attendance.meeting_center_id == meeting_center_id,
                        Attendance.class_code == class_code,
                        Attendance.sunday_date == sunday_date
                    )
                )
            )
            .distinct()
            .order_by(Attendance.student_name)
            .all()
        )
        # Extraemos los nombres que ya tienen asistencia registrada
        attendance_student_names = [record.student_name for record in attendance_members]

        # Calculamos los estudiantes que no han registrado asistencia
        non_attendance_students = [name for name in expected_student_names if name not in attendance_student_names]

        # Renderizamos los fragmentos HTML para cada tabla utilizando templates parciales.
        non_attendance_html = render_template(
            "partials/tables/non_attendance_table.html",
            non_attendance_students=non_attendance_students
        )
        with_attendance_html = render_template(
            "partials/tables/with_attendance_table.html",
            attendance_students=attendance_members
        )
       
        return jsonify({
            "non_attendance_html": non_attendance_html,
            "attendance_html": with_attendance_html,
            "message": "Attendance has been registered successfully."
        })
    # Para GET, renderizamos la plantilla principal
    return render_template('attendance_check.html', available_classes=available_classes)


# =============================================================================================
@bp.route("/attendance/filter", methods=['GET'])
@login_required
def filter_attendance():

    meeting_center_id = get_meeting_center_id()
    sunday_date = get_last_sunday()
    
    # Si sunday_date es una cadena, conviértela a date
    if isinstance(sunday_date, str):
        sunday_date = datetime.strptime(sunday_date, "%Y-%m-%d").date()

    time_range = request.args.get('time_range', 'last_two_weeks')

    if time_range == 'last_two_weeks':
        start_date = sunday_date - timedelta(weeks=2)
    elif time_range == 'last_month':
        start_date = sunday_date - timedelta(days=30)  # Aproximado a 30 días
    elif time_range == 'year_to_date':
        start_date = datetime(sunday_date.year, 1, 1)
    else:
        # Valor por defecto: últimas dos semanas
        start_date = sunday_date - timedelta(weeks=2)

    selected_class = request.args.get('class_code')

    if not selected_class:
        return jsonify({"error": "class_code parameter is missing."}), 400

    # Obtener los registros de asistencia para la clase seleccionada, en el meeting_center y fecha indicados
    attendance_members = (
        db.session.query(Attendance.student_name)
        .filter(
            Attendance.meeting_center_id == meeting_center_id,
            Attendance.class_code == selected_class,
            Attendance.sunday_date == sunday_date
        )
        .distinct()
        .order_by(Attendance.student_name)
        .all()
    )

    expected_student_names = (
        db.session.query(Attendance.student_name)
        .filter(
            Attendance.meeting_center_id == meeting_center_id,
            Attendance.class_code == selected_class,
            Attendance.sunday_date >= start_date,  # Filtramos por el rango de tiempo
            ~Attendance.student_name.in_(
                db.session.query(Attendance.student_name)
                .filter(
                    Attendance.meeting_center_id == meeting_center_id,
                    Attendance.class_code == selected_class,
                    Attendance.sunday_date == sunday_date
                )
            )
        )
        .distinct()
        .order_by(Attendance.student_name)
        .all()
    )
    # Extraemos los nombres que ya tienen asistencia registrada
    attendance_student_names = [record.student_name for record in attendance_members]

    # Calculamos los estudiantes que no han registrado asistencia
    non_attendance_students = [name for name in expected_student_names if name not in attendance_student_names]

    # Renderizamos los fragmentos HTML para cada tabla utilizando templates parciales.
    non_attendance_html = render_template(
        "partials/tables/non_attendance_table.html",
        non_attendance_students=non_attendance_students
    )
    attendance_html = render_template(
        "partials/tables/with_attendance_table.html",
        attendance_students=attendance_members
    )

    return jsonify({
        "non_attendance_html": non_attendance_html,
        "attendance_html": attendance_html
    })


# =============================================================================================
@bp.route("/classes_stats/percentage_data")
@role_required('Owner', 'Admin')
def get_classes_percentage_stats():
    meeting_center_id = get_meeting_center_id()
    current_year  = datetime.now().year
    selected_year = request.args.get('year', type=int, default=current_year)
    class_code1   = request.args.get("class_code1", default="all")
    class_code2   = request.args.get("class_code2", default="none")
    
    classes_to_compute = set()
    if class_code1 == "all":
        query = db.session.query(Attendance.class_code).distinct().filter(
            Attendance.meeting_center_id == meeting_center_id
        )
        for row in query.all():
            classes_to_compute.add(row.class_code)
    else:
        classes_to_compute.add(class_code1)
        if class_code2 != "none":
            classes_to_compute.add(class_code2)
    
    # Ordenar las clases para que el JS las asigne el mismo color siempre
    sorted_classes = sorted(classes_to_compute)
    
    result_data = []
    
    for code in sorted_classes:
        records = db.session.query(Attendance).filter(
            Attendance.class_code == code,
            Attendance.meeting_center_id == meeting_center_id,
            func.extract("year", Attendance.sunday_date) == selected_year
        ).order_by(Attendance.sunday_date).all()
        
        sessions = defaultdict(set)
        for rec in records:
            session_date = rec.sunday_date
            sessions[session_date].add(rec.student_name)
        
        sessions_by_month = defaultdict(list)
        for session_date, students in sessions.items():
            sessions_by_month[session_date.month].append((session_date, students))
        
        monthly_data = []
        for m in range(1, 13):
            if m in sessions_by_month and sessions_by_month[m]:
                sorted_sessions = sorted(sessions_by_month[m], key=lambda x: x[0])
                baseline = sorted_sessions[0][1]
                baseline_count = len(baseline)
                if baseline_count == 0:
                    monthly_data.append({"month": m, "percentage": None})
                    continue
                
                percentages = []
                for sess in sorted_sessions:
                    present = len(baseline.intersection(sess[1]))
                    percent = (present / baseline_count) * 100
                    percentages.append(percent)
                monthly_avg = round(sum(percentages) / len(percentages), 2)
                monthly_data.append({"month": m, "percentage": monthly_avg})
            else:
                monthly_data.append({"month": m, "percentage": None})
    
        translated_name = _(code)
        result_data.append({
            "class_code": code,
            "translated_name": translated_name,
            "chart_data": monthly_data
        })
    
    months = [{"value": value, "label": label} for value, label in get_months()]
    result_data = [r for r in result_data if any(item["percentage"] not in (None, 0) for item in r["chart_data"])]
    
    return jsonify({
        "chart_data": result_data,
        "months": months
    })


# =============================================================================================
@bp.route('/stats2/')
def stats():
    class_code = request.args.get('class_code', 'all')
    year = request.args.get('year', datetime.now().year)
    meeting_center_id = get_meeting_center_id()

    query = db.session.query(
        Attendance.sunday_date, Classes.class_code, db.func.count(Attendance.id)
    ).join(Classes).filter(Attendance.meeting_center_id == meeting_center_id)

    if class_code != 'all':
        query = query.filter(Attendance.class_code == class_code)

    year_start = datetime.strptime(f"{year}-01-01", "%Y-%m-%d")
    year_end = datetime.strptime(f"{year}-12-31", "%Y-%m-%d")
    query = query.filter(Attendance.sunday_date >= year_start, Attendance.sunday_date <= year_end)

    data = query.group_by(Attendance.sunday_date, Classes.class_code).all()

    chart_data = {}

    for date, class_code, count in data:
        date_str = date.strftime('%Y-%m-%d')
        if class_code not in chart_data:
            chart_data[class_code] = {}
        chart_data[class_code][date_str] = count

    # Obtener las fechas (labels) en orden
    labels = sorted(set(d for counts in chart_data.values() for d in counts))
    
    datasets = []
    # Iterar sobre las clases en orden alfabético
    for class_code in sorted(chart_data.keys()):
        date_counts = chart_data[class_code]
        data_points = [date_counts.get(label) for label in labels]
        datasets.append({
            "label": _(class_code),
            "data": data_points,
            "fill": False,
            "borderWidth": 1,
            "spanGaps": True
        })
    
    formatted_labels = [
        format_date(datetime.strptime(label, "%Y-%m-%d"), format='MMM dd')
        for label in labels
    ]

    return jsonify({
        'labels': formatted_labels,
        'datasets': datasets
    })

# =============================================================================================
@bp.route('/user/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()

    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

    if form.validate_on_submit():
        # Verificar si el email ya existe y no pertenece al usuario actual
        if User.query.filter(User.email == form.email.data, User.id != user.id).first():
            flash('Email already in use by another account.', 'danger')
            return redirect(url_for('profile'))

        user.email = form.email.data
        #user.name = form.name.data
        #user.lastname = form.lastname.data

        # Cambiar la contraseña si se ingresó una nueva
        if form.password.data:
            user.set_password(form.password.data)

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('routes.profile'))

    # Prellenar el formulario con los datos actuales del usuario
    form.username.data = user.username
    form.email.data    = user.email
    form.name.data     = user.name
    form.lastname.data = user.lastname

    return render_template('form.html',
                           form=form,
                           title=_('Edit User Profile'),
                           submit_button_text=_('Update Profile'),
                           clas='warning'
                           )