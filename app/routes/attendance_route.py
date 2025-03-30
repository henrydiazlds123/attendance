import csv
import io
from flask          import Blueprint, Response, jsonify, render_template, redirect, request, send_file, session, url_for, flash, make_response
from flask_babel    import gettext as _
from sqlalchemy     import func, extract, desc, asc, or_
from sqlalchemy.orm import joinedload
from app.config     import Config
from app.models     import db, Classes, Attendance, MeetingCenter, Setup, NameCorrections
from app.forms      import AttendanceEditForm, AttendanceForm
from urllib.parse   import unquote
from app.utils      import *
from datetime       import datetime, timedelta
from weasyprint     import HTML
from xhtml2pdf      import pisa

bp_attendance = Blueprint('attendance', __name__)

# =============================================================================================
@bp_attendance.route('/', methods=['GET', 'POST'])
def attendance():
    class_code  = request.args.get('classCode')
    sunday_code = request.args.get('sundayCode')
    unit_number = request.args.get('unitNumber')
    
    # if not class_code or not sunday_code or class_code not in CLASES:
    if not class_code or not sunday_code or not unit_number:
        return render_template('errors/4xx.html', 
                               page_title    = _('400 Invalid URL'),
                               error_number  = '400',
                               error_title   = _(_('Check what you wrote!')),
                               error_message = _('The address you entered is incomplete!')), 400

    code_verification_setting = Setup.query.filter_by(key='code_verification').first()
    code_verification_enabled = code_verification_setting.value if code_verification_setting else 'true'

    if code_verification_enabled == 'false':
        return render_template('attendance/attendance.html', 
                               class_code  = class_code,
                               sunday_code = sunday_code,
                               sunday      = get_next_sunday(),
                               unit_number = unit_number)
    
    expected_code = get_next_sunday_code(get_next_sunday())
    if int(sunday_code) == expected_code:
        return render_template('attendance/attendance.html', 
                               class_code  = class_code,
                               sunday_code = sunday_code,
                               sunday      = get_next_sunday(),
                               unit_number = unit_number)
    else:
        return render_template('errors/4xx.html', 
                               page_title    = '403 Incorrect QR',
                               error_number  = '403',
                               error_title   = _('It seems that you are lost!'),
                               error_message = _("Wrong QR for this week's classes!")), 403
    

# =============================================================================================
@bp_attendance.route('/list', methods=['GET', 'POST'])
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
            'attendance/list_table.html',
            attendances     = attendances_formatted,
            has_records     = has_records,
            total_registros = total_registros,
            corrected_names = corrected_names,
            pagination      = attendances
        )
    else:
        # Si no es AJAX, renderizar la plantilla completa
        return render_template(
            'attendance/list.html',
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
@bp_attendance.route('/new', methods=['GET', 'POST'])
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
            return render_template('form/form.html', 
                                   form               = form,
                                   title              = _('Create manual attendance'),
                                   submit_button_text = _('Create'),
                                   clas               = 'warning')

        sunday_code = '0000' # Indica que la clase fue entrada manualmente, no usando QR 

        # Obtener el class_code basado en el class_id seleccionado
        selected_class = Classes.query.filter_by(id=form.class_id.data).first()
        if not selected_class:
            flash(_('The selected class is invalid.'), 'danger')
            return render_template('form/form.html', 
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
        return redirect(url_for('attendance.attendances'))

    return render_template('form/form.html', 
                           form               = form,
                           title              = _('Create manual attendance'),
                           submit_button_text = _('Create'),
                           clas               = 'warning')


# =============================================================================================
@bp_attendance.route('/edit/<int:id>', methods=['GET', 'POST'])
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
        return redirect(url_for('attendance.attendances', **request.args.to_dict()))

    return render_template('form/form.html', form=form, title=_('Edit Attendance'), submit_button_text=_('Update'), clas='warning')


# =============================================================================================
@bp_attendance.route('/delete/<int:id>', methods=['GET', 'POST'])
@role_required('Admin', 'Super', 'Owner')
def delete_attendance(id):
    
    attendance = Attendance.query.get_or_404(id)
    db.session.delete(attendance)
    db.session.commit()
    flash(_('Attendance record deleted successfully.'), 'success')
    return redirect(url_for('attendance.attendances', **request.args.to_dict()))


# =============================================================================================
@bp_attendance.route('/manual')
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
    return render_template('attendance/manual.html', class_links=class_links)


# =============================================================================================
@bp_attendance.route('/report')
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
            "attendance/report_table.html", 
            students       = students,
            dates          = sunday_dates_formatted,
            total_miembros = total_miembros
        )

    return render_template(
        'attendance/report.html',
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
@bp_attendance.route('/report/pdf')
@login_required
def attendance_report_pdf():
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

    # Generar PDF
    rendered_html = render_template(
        'attendance/report_table.html',
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
    

    pdf = io.BytesIO()
    pisa.CreatePDF(io.BytesIO(rendered_html.encode("UTF-8")), pdf)
    pdf.seek(0)

    return send_file(pdf, mimetype='application/pdf', as_attachment=False, download_name="attendance_report.pdf")


# =============================================================================================
@bp_attendance.route('/export', methods=['GET'])
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
@bp_attendance.route('/monthly/<student_name>')
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
@bp_attendance.route("/check", methods=['POST', 'GET'])
@login_required
def register_attendance():
    meeting_center_id = get_meeting_center_id()
    sunday_date_str   = get_last_sunday()  # Retorna una cadena, e.g. "2025-02-09"
    
    sunday_date       = datetime.strptime(sunday_date_str, "%Y-%m-%d").date()
    sunday_week       = (get_next_sunday().day - 1) // 7 + 1
    role              = session.get('role')
    organization_id   = session.get('organization_id')

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
                student_name      = student_name,
                class_id          = cls.id,
                sunday_date       = sunday_date,
                meeting_center_id = meeting_center_id
            ).first()
            if not existing:
                new_attendance = Attendance(
                    student_name      = student_name,
                    class_id          = cls.id,
                    class_code        = class_code,
                    sunday_date       = sunday_date,       # Objeto date
                    sunday_code       = 1111,
                    meeting_center_id = meeting_center_id,
                    submit_date       = datetime.now(),
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
                or_(Attendance.class_code == class_code, class_code == "FS"),  # Permite incluir todos si class_code es "FS"
                Attendance.sunday_date >= start_date,
                ~Attendance.student_name.in_(
                    db.session.query(Attendance.student_name)
                    .filter(
                        Attendance.meeting_center_id == meeting_center_id,
                        or_(Attendance.class_code == class_code, class_code == "FS"),
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
            "admin/non_attendance.html",
            non_attendance_students=non_attendance_students
        )
        with_attendance_html = render_template(
            "admin/with_attendance.html",
            attendance_students=attendance_members
        )
       
        return jsonify({
            "non_attendance_html": non_attendance_html,
            "attendance_html": with_attendance_html,
            "message": "Attendance has been registered successfully."
        })
    # Para GET, renderizamos la plantilla principal
    return render_template('attendance/check.html', available_classes=available_classes)


# =============================================================================================
@bp_attendance.route("/filter", methods=['GET'])
@login_required
def filter_attendance():

    meeting_center_id = get_meeting_center_id()
    sunday_date = get_last_sunday()


    
    # Si sunday_date es una cadena, conviértela a date
    if isinstance(sunday_date, str):
        sunday_date = datetime.strptime(sunday_date, "%Y-%m-%d").date()

    time_range = request.args.get('time_range', 'last_two_weeks')

    if time_range == 'previous_week':
        start_date = sunday_date - timedelta(weeks=1)
    elif time_range == 'last_two_weeks':
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
            or_(Attendance.class_code == selected_class, selected_class == "FS"),  # Permite incluir todos si class_code es "FS"
            Attendance.sunday_date >= start_date,
            ~Attendance.student_name.in_(
                db.session.query(Attendance.student_name)
                .filter(
                    Attendance.meeting_center_id == meeting_center_id,
                    or_(Attendance.class_code == selected_class, selected_class == "FS"),
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
        "admin/non_attendance.html",
        non_attendance_students=non_attendance_students
    )
    attendance_html = render_template(
        "admin/with_attendance.html",
        attendance_students=attendance_members
    )

    return jsonify({
        "non_attendance_html": non_attendance_html,
        "attendance_html": attendance_html
    })