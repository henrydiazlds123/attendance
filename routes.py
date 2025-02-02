import qrcode
from flask                   import Blueprint, abort, jsonify, render_template, redirect, request, session, url_for, flash, send_from_directory, send_file
from flask_babel             import gettext as _
from sqlalchemy              import func, extract
from config                  import Config
from models                  import db, Classes, User, Attendance, MeetingCenter, Setup, Organization, NameCorrections
from forms                   import AttendanceEditForm, AttendanceForm, MeetingCenterForm, UserForm, EditUserForm, ResetPasswordForm, ClassForm, OrganizationForm
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils     import ImageReader
from reportlab.pdfgen        import canvas
from urllib.parse            import unquote
from utils                   import *
from sqlalchemy.exc          import IntegrityError
from datetime                import datetime, timedelta
from io                      import BytesIO



bp = Blueprint('routes', __name__)




@bp.before_request
def load_user():
    # Verifica si hay un ID de usuario en la sesión y carga el usuario
    user_id = session.get('user_id')
    if user_id:
        g.user = User.query.get(user_id)  # Asumiendo que tienes un modelo `User`
    else:
        g.user = None

# =============================================================================================
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
            session['organization_id']       = user.organization_id
            
            print(user.organization_id)
            
            if session['role'] == 'Operator':
                return redirect(url_for('routes.manual_attendance'))
            if session['role'] == 'Owner':
                return redirect(url_for('routes.admin'))

            flash(_('Login successful!'), 'success')
            return redirect(url_for('routes.attendance_report'))
        else:
            flash(_('Invalid credentials. Please check your username and password..'), 'danger')
    return render_template('login.html')


# =============================================================================================
@bp.route('/logout')
def logout():
    session.clear()
    flash(_('Logout successful!'), 'success')
    return redirect(url_for('routes.login'))


# =============================================================================================
@bp.route('/reset_name')
def reset_name():
    """Renderiza una página para mostrar el nombre almacenado y borrarlo con confirmación."""
    return render_template('reset_name.html')


# =============================================================================================
@bp.route('/')
def index():
    return render_template('index.html')
    # return redirect('/login', code=302)


# =============================================================================================
@bp.route('/users')
@role_required('Admin', 'Owner')
def users():
    role = session.get('role')
    meeting_center_id = session.get('meeting_center_id')
    admin_count = User.query.filter_by(role='Admin').count()

    if role == 'Owner':
    # Owners can see all users
        query = db.session.query(
            User.id,
            User.username,
            User.email,
            User.role,
            MeetingCenter.short_name.label('meeting_short_name'),
            Organization.name.label('organization_name')
        ).join(MeetingCenter, User.meeting_center_id == MeetingCenter.id) \
            .join(Organization, User.organization_id == Organization.id)

        users = query.all()
    elif role == 'Admin':
        # Admins can only see users in their organization, excluding Owners
        users = db.session.query(
            User.id,
            User.username,
            User.email,
            User.role,
            Organization.name.label('organization_name')
        ).join(MeetingCenter, User.meeting_center_id == MeetingCenter.id) \
        .join(Organization, User.organization_id == Organization.id) \
        .filter(User.role != 'Owner') \
        .filter(User.organization_id == session.get('organization_id')).all()
    else:
        # Regular users can only see their own user
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
    return render_template('form.html', form=form, title=_('New User'), submit_button_text=_('Create'), clas='warning')


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
        flash(_('User updated successfully.'), 'success')
        return redirect(url_for('routes.users'))
    return render_template('form.html', form=form, title=_('Edit User'), submit_button_text=_('Update'), clas='warning')


# =============================================================================================
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
            return render_template('form.html', form=form, title="Reset Password", submit_button_text="Update", clas="danger")

        user.set_password(form.new_password.data)
        db.session.commit()
        flash(_('Password updated successfully.'), 'success')
        return redirect(url_for('routes.users'))

    return render_template('form.html', form=form, title="Change Password", submit_button_text="Update", clas="danger")


# =============================================================================================
@bp.route('/users/<int:id>/promote', methods=['POST'])
@role_required('Owner')
def promote_to_admin(id):
    user = User.query.get_or_404(id)
    if user.role =='Admin':
        flash(_('The user is already an administrator.'), 'info')
    else:
        user.role = 'Admin'
        db.session.commit()
        # flash(f'El usuario {user.username} ha sido promovido a administrador.', 'success')
        flash(_('User %(username)s has been promoted to administrator.') % {'username': user.username}, 'success')
    return redirect(url_for('routes.users'))


# =============================================================================================
@bp.route('/attendance', methods=['GET', 'POST'])
def attendance():
    class_code  = request.args.get('class')
    sunday_code = request.args.get('code')
    unit_number = request.args.get('unit')
    
    print(class_code, unit_number, sunday_code)

    # if not class_code or not sunday_code or class_code not in CLASES:
    if not class_code or not sunday_code or not unit_number:
        return render_template('4xx.html', page_title=_('400 Invalid URL'), error_number='400', error_title=_(_('Check what you wrote!')), error_message=_('The address you entered is incomplete!')), 400

    code_verification_setting = Setup.query.filter_by(key='code_verification').first()
    code_verification_enabled = code_verification_setting.value if code_verification_setting else 'true'

    if code_verification_enabled == 'false':
        return render_template('attendance.html', class_code=class_code, sunday_code=sunday_code, sunday=get_next_sunday(),unit_number=unit_number)
    
    expected_code = get_next_sunday_code(get_next_sunday())
    if int(sunday_code) == expected_code:
        return render_template('attendance.html', class_code=class_code, sunday_code=sunday_code, sunday=get_next_sunday(),unit_number=unit_number)
    else:
        return render_template('4xx.html', page_title='403 Incorrect QR', error_number='403', error_title=_('It seems that you are lost!'), error_message=_("Wrong QR for this week's classes!")), 403
    

# =============================================================================================
@bp.route('/attendance/list', methods=['GET', 'POST'])
@role_required('User', 'Admin', 'Owner')
def attendances():
    # Get user role and meeting_center_id from session
    role              = session.get('role')
    months_abr        = get_months()
    meeting_center_id = session.get('meeting_center_id')
    corrected_names   = [
        correction.correct_name 
        for correction in NameCorrections.query.filter_by(meeting_center_id=meeting_center_id).all()
    ]

    # Get distinct values for filters
    classes  = db.session.query(Classes.id, Classes.short_name).join(Attendance, Attendance.class_id == Classes.id).distinct().filter(Classes.meeting_center_id == session.get('meeting_center_id')).all()
    students = db.session.query(Attendance.student_name.distinct()).filter(Attendance.meeting_center_id == session.get('meeting_center_id')).all()
    sundays  = db.session.query(Attendance.sunday_date.distinct()).filter(Attendance.meeting_center_id == session.get('meeting_center_id')).all()

    # Formatear las fechas con Flask-Babel
    sundays_formatted = [
        {"date": sunday[0], "formatted": format_date(sunday[0], format='MMM dd')}  # 'MMM dd' para "Mes día"
        for sunday in sundays
    ]

    # Get filter parameters from URL query string
    class_name    = request.args.get('class_name')
    student_name  = request.args.get('student_name')
    sunday_date   = request.args.get('sunday_date')

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
    attendances     = query.order_by(Attendance.student_name, Attendance.sunday_date, Attendance.class_id) \
        .filter(Attendance.meeting_center_id == session.get('meeting_center_id')).all()
    
    # Formatear las fechas con Flask-Babel
    attendances_formatted = [
        {
            **attendance._asdict(),  # Convertir el objeto SQLAlchemy a un diccionario
            "sunday_date_formatted": format_date(attendance.sunday_date, format='MMM dd')  # Formatear la fecha
        }
        for attendance in attendances
    ]

    total_registros = len(attendances)
    has_records     = Attendance.query.count() > 0

    
    
    return render_template(
        'attendance_list.html', 
        attendances     = attendances_formatted,
        has_records     = has_records,
        classes         = classes,
        students        = students,
        sundays         = sundays_formatted,     # Usar las fechas formateadas
        months          = months,
        years           = years,
        total_registros = total_registros,
        months_abr      = months_abr,
        corrected_names = corrected_names
    )


# =============================================================================================
@bp.route('/attendance/new', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def create_attendance():
    form                           = AttendanceForm()
    form.class_id.choices          = [(c.id, c.translated_name) for c in Classes.query.filter_by(meeting_center_id=session.get('meeting_center_id')).all()]
    form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]

    if request.method == 'GET':
        form.set_default_sunday_date() 

    # Populate student name choices dynamically with current student names
    existing_students          = db.session.query(Attendance.student_name).filter(Attendance.meeting_center_id == session['meeting_center_id']).distinct().all()
    form.student_name.choices += [(name[0], name[0]) for name in existing_students]
    

    if form.validate_on_submit():
        # Determine whether to use an existing student name or a new one
        student_name = form.new_student_name.data.strip() if form.new_student_name.data else form.student_name.data

        # Check if no name was provided in either field
        if not student_name:
            flash(_('Please select an existing student or provide a new name.'), 'danger')
            return render_template('form.html', form=form, title=_('Create manual attendance'), submit_button_text=_('Create'), clas='warning')

        # Calculate sunday_code based on the provided sunday date
        # sunday_code = get_next_sunday_code(form.sunday_date.data)
        sunday_code = '0000'
        
        # Obtener el class_code basado en el class_id seleccionado
        selected_class = Classes.query.filter_by(id=form.class_id.data).first()
        if not selected_class:
            flash(_('The selected class is invalid.'), 'danger')
            return render_template('form.html', form=form, title=_('Create attendance'), submit_button_text=_('Create'), clas='warning')

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

    return render_template('form.html', form=form, title=_('Create manual attendance'), submit_button_text=_('Create'), clas='warning')


# =============================================================================================
@bp.route('/attendance/edit/<int:id>', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def update_attendance(id):
    attendance = Attendance.query.get_or_404(id)
    form = AttendanceEditForm(obj=attendance)
    
    # Obtener el meeting_center_id relacionado con la asistencia (puede ser del usuario o de otra fuente)
    meeting_center_id = attendance.meeting_center_id  # O de donde sea necesario

    # Filtrar las clases por el meeting_center_id
    form.class_id.choices = [(c.id, c.translated_name) for c in Classes.query.filter_by(meeting_center_id=meeting_center_id).all()]

    if form.validate_on_submit():
        attendance.student_name = form.student_name.data
        attendance.class_id     = form.class_id.data
        attendance.sunday_date  = form.sunday_date.data

        db.session.commit()
        flash(_('Attendance record updated successfully.'), 'success')
        return redirect(url_for('routes.attendances', **request.args.to_dict()))

    return render_template('form.html', form=form, title=_('Edit Attendance'), submit_button_text=_('Update'), clas='warning')


# =============================================================================================
@bp.route('/attendance/delete/<int:id>', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def delete_attendance(id):
    
    attendance = Attendance.query.get_or_404(id)
    db.session.delete(attendance)
    db.session.commit()
    flash(_('Attendance record deleted successfully.'), 'success')
    return redirect(url_for('routes.attendances', **request.args.to_dict()))


# =============================================================================================
@bp.route('/attendance/manual')
# @role_required('User', 'Admin', 'Owner', 'Operator')
def manual_attendance():
    """Genera enlaces solo para las clases correspondientes al próximo domingo."""
    next_sunday_code = get_next_sunday_code(get_next_sunday())
    sunday_week      = (get_next_sunday().day - 1) // 7 + 1  # Determina la semana del mes
    unit             = session['meeting_center_number']
        
    # Generar enlaces solo para las clases correspondientes
    class_links = {
        class_entry.class_code: {
            'url': f"{Config.BASE_URL}/attendance/manual?class_name={class_entry.translated_name}&class={class_entry.class_code}&code={next_sunday_code}&unit={unit}",
            'name': class_entry.class_name
        }
        for class_entry in Classes.query.filter_by(is_active=True).all() if str(sunday_week) in class_entry.schedule.split(',')
    }
    return render_template('manual_attendance.html', class_links=class_links)


# =============================================================================================
@bp.route('/attendance/report')
@login_required
def attendance_report():
    meeting_center_id = get_meeting_center_id()

    if meeting_center_id == 'all':
        meeting_center_id = None  # No aplicar filtro

    current_year  = datetime.now().year
    current_month = datetime.now().month

    # Obtener años y meses disponibles, manejando el caso donde `meeting_center_id` es `None`
    year_query  = db.session.query(func.extract('year', Attendance.sunday_date)).distinct().order_by(func.extract('year', Attendance.sunday_date))
    month_query = db.session.query(func.extract('month', Attendance.sunday_date)).distinct().order_by(func.extract('month', Attendance.sunday_date))

    if meeting_center_id is not None:
        year_query  = year_query.filter(Attendance.meeting_center_id == meeting_center_id)
        month_query = month_query.filter(Attendance.meeting_center_id == meeting_center_id)

    available_years  = [y[0] for y in year_query.all() if y[0] is not None]
    available_months = [m[0] for m in month_query.all() if m[0] is not None]
    month_names      = [{"num": m, "name": _(datetime(2000, m, 1).strftime('%b'))} for m in available_months]

    selected_year  = request.args.get('year', type=int, default=current_year)
    selected_month = request.args.get('month', type=int, default=current_month)

    # Verificar si hay datos en el mes actual
    query = db.session.query(Attendance.sunday_date).distinct().order_by(Attendance.sunday_date)
    if meeting_center_id is not None:
        query = query.filter(Attendance.meeting_center_id == meeting_center_id)
    query = query.filter(extract('year', Attendance.sunday_date) == selected_year)
    query = query.filter(extract('month', Attendance.sunday_date) == selected_month)

    sundays = query.all()
    sunday_dates = [s[0] for s in sundays]

    # Si no hay datos en el mes actual, cambiar al mes anterior
    if not sunday_dates:
        selected_month -= 1
        if selected_month < 1:
            selected_month = 12
            selected_year -= 1

        # Rehacer la consulta con el nuevo mes
        query = db.session.query(Attendance.sunday_date).distinct().order_by(Attendance.sunday_date)
        if meeting_center_id is not None:
            query = query.filter(Attendance.meeting_center_id == meeting_center_id)
        query = query.filter(extract('year', Attendance.sunday_date) == selected_year)
        query = query.filter(extract('month', Attendance.sunday_date) == selected_month)

        sundays = query.all()
        sunday_dates = [s[0] for s in sundays]

    # Limitar los datos a 5 semanas
    sunday_dates = sunday_dates[-5:]

    # Formatear las fechas con Flask-Babel
    sunday_dates_formatted = [
        {"date": date, "formatted": format_date(date, format='MMM dd')}  # 'MMM dd' para "Mes día"
        for date in sunday_dates
    ]

    # Obtener registros de asistencia
    attendance_query = db.session.query(Attendance).order_by(Attendance.student_name, Attendance.sunday_date)

    if meeting_center_id is not None:
        attendance_query = attendance_query.filter(Attendance.meeting_center_id == meeting_center_id)

    attendance_query = attendance_query.filter(extract('year', Attendance.sunday_date) == selected_year)
    attendance_query = attendance_query.filter(extract('month', Attendance.sunday_date) == selected_month)

    attendance_records = attendance_query.all()

    # Construcción del diccionario de asistencia
    students = {}
    for record in attendance_records:
        if record.student_name not in students:
            students[record.student_name] = {date['date']: False for date in sunday_dates_formatted}
        students[record.student_name][record.sunday_date] = True

    total_miembros = len(students)

    # Si la solicitud es AJAX, devolver solo la parte de la asistencia
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("partials/attendance_table.html", students=students, dates=sunday_dates_formatted)

    return render_template(
        'attendance_report.html',
        students         = students ,
        dates            = sunday_dates_formatted , # Usar las fechas formateadas
        available_years  = available_years ,
        available_months = month_names ,
        selected_year    = selected_year ,
        selected_month   = selected_month ,
        total_miembros   = total_miembros ,
        disable_month    = len(available_months)  == 1,
        disable_year     = len(available_years)   == 1
    )
    
    
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
@bp.route('/registrar', methods=['POST'])
def registrar():
    try:
        student_name   = request.form.get('studentName').title()
        class_code     = request.form.get('classCode')
        sunday_date    = get_next_sunday()
        sunday_code    = request.form.get('sundayCode')
        unit_number    = request.form.get('unitNumber')

        nombre, apellido = student_name.split(" ", 1)
        formatted_name = f"{apellido}, {nombre}"
        print(f"class_code {class_code})")

        # Verificar si la clase es válida
        class_entry = Classes.query.filter_by(class_code=class_code).first()
        if not class_entry:
            return jsonify({
                "success": False,
                "message": _('The selected class is not valid.'),
            }), 400

        # Verificar si el Meeting Center es válido
        meeting_center = MeetingCenter.query.filter_by(unit_number=unit_number).first()
        if not meeting_center:
            return jsonify({
                "success": False,
                "message": _('The church unit is invalid.'),
            }), 400

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
                        }), 400

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
                    }), 400

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

        # Registrar la asistencia
        new_attendance = Attendance(
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
@bp.route('/pdf/generate_all', methods=['GET', 'POST'])
@login_required
def generate_all_pdfs():
    return redirect(url_for('routes.generate_pdfs', type='todos'))  # redirige a la misma función con parámetro "todos"


# =============================================================================================
@bp.route('/pdf/generate_week', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def generate_week_pdfs():
    return redirect(url_for('routes.generate_pdfs', type='semana_especifica'))  # redirige a la misma función para PDFs de la semana específica


# =============================================================================================
@bp.route('/pdf/generate_extra', methods=['GET', 'POST'])
@login_required
def generate_extra_pdfs():
    selected_date = request.form.get('date')  # Obtener la fecha desde el formulario
    print(f'Date: {selected_date}')

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
    print(f"User-provided date: {user_date}")  # Debugging
    
    OUTPUT_DIR = get_output_dir()
    print(f"Output directory: {OUTPUT_DIR}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Función auxiliar para obtener la fecha de la clase
    def get_class_date(class_type, user_date=None):
        if class_type == 'Main':
            return get_next_sunday()  # Fecha del próximo domingo
        elif class_type == 'Extra' and user_date:
            try:
                class_date = datetime.strptime(user_date, '%Y-%m-%d')
                if class_date.date() >= datetime.today().date():
                    return class_date
                else:
                    raise ValueError(_('The date must be today or in the future.'))
            except ValueError as e:
                flash(str(e), 'error')
                print(f"Error parsing date: {e}")
                return None
        else:
            flash(_('Invalid date for extra class.'), 'error')
            print('Invalid date for extra class.')
            return None

    # Obtener el ID del meeting center desde la sesión
    next_sunday_code  = get_next_sunday_code(get_next_sunday())
    meeting_center_id = session['meeting_center_id']
    unit_name         = session['meeting_center_name']
    unit              = session['meeting_center_number']
    sunday_week       = (get_next_sunday().day - 1) // 7 + 1

    # Obtener las clases filtradas por meeting center
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

    print(f"Classes to print for meeting center {meeting_center_id}: {[c.class_name for c in clases_a_imprimir]}")

    clean_qr_folder(OUTPUT_DIR)
    print("QR folder cleaned.")

    for class_entry in clases_a_imprimir:
        if class_entry.class_type == 'Extra' and not user_date:
            print(f"No date provided for extra class: {class_entry.class_name}")
            continue

        class_date = get_class_date(class_entry.class_type, user_date)
        if not class_date:
            print(f"Skipping class {class_entry.class_name} due to invalid date.")
            continue

        class_name  = class_entry.translated_name
        class_code  = class_entry.class_code
        class_color = class_entry.class_color or "black"

        qr_url = f"{Config.BASE_URL}/attendance?class_name={class_name.replace(' ', '+')}&code={next_sunday_code}&date={class_date.strftime('%Y-%m-%d')}&unit={unit}&class={class_code}"
        print(f"QR URL for {class_name}: {qr_url}")

        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=class_color, back_color="white")

        qr_filename = os.path.join(OUTPUT_DIR, f"{class_name}_{format_date(class_date)}.png")
        img.save(qr_filename)
        print(f"QR code saved: {qr_filename}")

        pdf_filename = os.path.join(OUTPUT_DIR, f"{_(class_name)}_{format_date(class_date)}.pdf")
        c = canvas.Canvas(pdf_filename, pagesize=letter)
        page_width, page_height = letter

        c.setFont("Helvetica-Bold", 24)
        c.setFillColor("black")
        c.drawCentredString(page_width / 2, 670, _(f"Attendance Sheet"))
        c.setFont("Helvetica-Bold", 35)
        c.drawCentredString(page_width / 2, 625, _(class_name))

        qr_image = ImageReader(qr_filename)
        qr_size = 430
        qr_x = (page_width - qr_size) / 2
        qr_y = (page_height - qr_size) / 2
        c.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)

        c.setFont("Helvetica", 18)
        c.setFillColor("black")
        c.drawCentredString(page_width / 2, qr_y - 15, unit_name)
        c.drawCentredString(page_width / 2, qr_y - 40, f"{format_date(class_date)}")
        c.save()
        print(f"PDF saved: {pdf_filename}")

    clean_qr_images(OUTPUT_DIR)
    print("QR images cleaned.")

    flash(_('QR Codes generated successfully.'), 'success')
    return redirect(url_for('routes.list_pdfs'))


# =============================================================================================
@bp.route('/pdf/download/<path:filename>', methods=['GET'])
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
@role_required('Admin', 'Owner')
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
@role_required('Owner')
def get_meeting_centers():
    meeting_centers = MeetingCenter.query.order_by(MeetingCenter.name).all()
    return jsonify([
        {"id": mc.id, "name": mc.name}
        for mc in meeting_centers
    ])




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
            class_name          = form.class_name.data,
            short_name          = form.short_name.data,
            class_code          = form.class_code.data,
            class_type          = form.class_type.data,
            schedule            = form.schedule.data,
            is_active           = form.is_active.data,
            class_color         = form.class_color.data,
            meeting_center_id   = form.meeting_center_id.data
        )
        try:
            db.session.add(new_class)
            db.session.commit()
            flash(_('Class created successfully!'), 'success')
            return redirect(url_for('routes.classes'))
        except IntegrityError:
            db.session.rollback()
            flash(_('A class with this name, short name, or code already exists in the same church unit.'), 'danger')
    return render_template('form.html', form=form, title=_('Create New Class'), submit_button_text=_('Create'), clas='warning')


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
            flash(_('Class updated successfully!'), 'success')
            return redirect(url_for('routes.classes'))
        except IntegrityError:
            db.session.rollback()
            flash(_('A class with this name, short name, or code already exists in the same church unit.'), 'danger')
    return render_template('form.html', form=form, title=_('Edit Class'), submit_button_text=_('Update'), clas='warning', backroute='classes')


# =============================================================================================
@bp.route('/classes/delete/<int:id>', methods=['POST'])
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
        'alreadyRegistered'     : _('You already have registered assistance on {sunday_date}.'),
        'actionCanceled'        : _('Action canceled'),
        'attendanceRecorded'    : _('¡{student_name}, your attendance was recorded!'),
        'cancel'                : _('Cancel'),
        'cancelled'             : _('Cancelled'),
        'cancelledMessage'      : _('No correction has been made.'),
        'chooseClass'           : _('Choose a Class'),
        'cleared'               : _('Cleared!'),
        'confirm'               : _('Confirm'),
        'confirmDelete'         : _('You \'re sure?'),
        'connectionError'       : _('There was a problem connecting to the server.'),
        'deleteConfirmationText': _('This action will delete all records and cannot be undone.'),
        'deleteOneRecordText   ': _('This record will be deleted.'),
        'errorTitle'            : _('Error'),
        'errorMessage'          : _('There was a problem saving the correction'),
        'great'                 : _('Great!'),
        'incorrectPatternLabel' : _('Incorrect format'),
        'incorrectPatternText'  : _('The name must be in the format "Last Name, First Name", separated by a comma.'),
        'mustSelectDate'        : _('You must select a date!'),
        'nameFormatText'        : _('Please enter your name in \'First Name Last Name\' format.'),
        'nameNotRemoved'        : _('Your name was not removed.'),
        'nameRemoved'           : _('The name has been removed.'),
        'noNameFound'           : _('No Name Found'),
        'noNameSaved'           : _('No name is currently saved.'),
        'noQrGenerated'         : _('QR codes were not generated'),
        'resetStudentName'      : _('Reset Student Name'),
        'savedNameText'         : _('The saved name is: \'{name}\'. Do you want to clear it?'),
        'revertTitle'           : _('Are you sure you want to revert this correction?'),
        'revertConfirmButton'   : _('Revert'),
        'selectDateExtraClasses': _('Select a date for Extra classes'),
        'sundayClassRestriction': _('You cannot register a \'Sunday Class\' outside of Sunday.'),
        'yes'                   : _('Yes'),
        'yesDeleteEverything'   : _('Yes, delete everything'),
        'yesClearIt'            : _('Yes, clear it!'),
        'yesDeleteIt'           : _('Yes, Delete it!'),
        'warningTitle'          : _('warning'),
        'wrongNameTitle'        : _('Please enter the correct name'),
        'wrongNameText'         : _('Please enter the correct name for '),
        'wrongNameLabel'        : _('Correct Format: Last Name, First Name'),
        'wrongNamePlaceholder'  : _('Enter the new name'),
        'confirmSave'           : _('Confirm'),
        'successTitle'          : _('¡Success'),
        'successMessage'        : _('The name has been corrected'),
    }
    
    
# =============================================================================================   
@bp.route('/classes/populate/<int:id>', methods=['GET', 'POST'])
@role_required('Owner')
def populate_classes(id):
    new_meeting_center_id = id

    # Arreglo estático con las clases tipo Main
    main_classes_static = [
        {
            'class_name': _('Elders Quorum'),
            'short_name': _('Elders_Q'),
            'class_code': 'EQ',
            'class_type': _('Main'),
            'schedule'  : '2,4',
            'is_active' : True,
            'class_color': None  # Esto se puede ajustar en el futuro
        },
        {
            'class_name': _('Aaronic Priesthood'),
            'short_name': _('Aaronic_P'),
            'class_code': 'AP',
            'class_type': _('Main'),
            'schedule'  : '2,4',
            'is_active' : True,
            'class_color': None
        },
        {
            'class_name': _('Relief Society'),
            'short_name': _('Relief_S'),
            'class_code': 'RS',
            'class_type': _('Main'),
            'schedule'  : '2,4',
            'is_active' : True,
            'class_color': '#ba8e23'
        },
        {
            'class_name': _('Young Woman'),
            'short_name': _('Young_W'),
            'class_code': 'YW',
            'class_type': _('Main'),
            'schedule'  : '2,4',
            'is_active' : True,
            'class_color': '#943f88'
        },
        {
            'class_name': _('Sunday School Adults'),
            'short_name': _('S_S_Adults'),
            'class_code': 'SSA',
            'class_type': _('Main'),
            'schedule'  : '1,3',
            'is_active' : True,
            'class_color': None
        },
        {
            'class_name': _('Sunday School Youth'),
            'short_name': _('S_S_Youth'),
            'class_code': 'SSY',
            'class_type': _('Main'),
            'schedule'  : '1,3',
            'is_active' : True,
            'class_color': None
        },
        {
            'class_name': _('Fifth Sunday'),
            'short_name': _('F_Sunday'),
            'class_code': 'FS',
            'class_type': _('Main'),
            'schedule'  : '5',
            'is_active' : True,
            'class_color': None
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
                class_name        = class_data['class_name'],
                short_name        = class_data['short_name'],
                class_code        = class_data['class_code'],
                class_type        = class_data['class_type'],
                schedule          = class_data['schedule'],
                is_active         = class_data['is_active'],
                class_color       = class_data['class_color'],
                meeting_center_id = new_meeting_center_id
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
@role_required('Admin', 'Owner')
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
@role_required('Admin', 'Owner')
def admin():
    meeting_center_id = get_meeting_center_id()
    
    if meeting_center_id == 'all':
        meeting_center_id = None  # No aplicar filtro
        name_corrections = NameCorrections.query.all()
        
    if meeting_center_id is not None:
        name_corrections = NameCorrections.query.filter(NameCorrections.meeting_center_id == meeting_center_id).all()  # Obtener todos los registros de NameCorrect
    
    # Get the configuration for code verification setting
    code_verification_setting = Setup.query.filter_by(key='code_verification').first()
    bypass_enabled = request.args.get('bypass_enabled', 'false')  # Default "false"
    
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

        return redirect(url_for('routes.admin'))
   
    verification_enabled = code_verification_setting.value if code_verification_setting else 'true'
    
    return render_template('admin.html', 
                           verification_enabled=verification_enabled, 
                           bypass_enabled=bypass_enabled, 
                           name_corrections=name_corrections
                           )


# =============================================================================================
@bp.route('/admin/bypass', methods=['POST'])
def update_bypass_restriction():
    new_value = request.form.get('bypass_restriction', 'false')  # Default "false"

    # Buscar el registro en la base de datos
    bypass_entry = Setup.query.filter_by(key='bypass_restriction').first()

    if bypass_entry:
        bypass_entry.value = new_value  # Actualiza el valor
    else:
        bypass_entry = Setup(key='bypass_restriction', value=new_value)
        db.session.add(bypass_entry)  # Crea un nuevo registro si no existe

    db.session.commit()  # Guarda los cambios

    flash("Bypass restriction updated successfully!", "success")
    return redirect(url_for('routes.admin', bypass_enabled=new_value))


# =============================================================================================
@bp.route('/admin/name_correction/delete/<int:id>', methods=['POST'])
def delete_name_correction(id):
    correction = NameCorrections.query.get_or_404(id)  # Buscar el registro por ID
    db.session.delete(correction)  # Eliminar el registro
    db.session.commit()  # Guardar los cambios
    flash("Name correction deleted successfully!", "success")
    return redirect(url_for('routes.admin'))  # Redirigir a la vista admin


# =============================================================================================
@bp.route('/admin/name_correction/revert/<int:id>', methods=['POST'])
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

    flash("Name correction reverted successfully!", "success")
    return redirect(url_for('routes.admin'))


# =============================================================================================
@bp.route('/admin/name_corrections/filter', methods=['GET'])
def filter_name_corrections():
    meeting_center_id = request.args.get('meeting_center_id', type=int)
    
    if meeting_center_id == 'all' or meeting_center_id is None:
        name_corrections = NameCorrections.query.all()
    else:
        name_corrections = NameCorrections.query.filter_by(meeting_center_id=meeting_center_id).all()
    
    return render_template('partials/name_correction_table.html', name_corrections=name_corrections)


# =============================================================================================
@bp.route('/api/admin_data')
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