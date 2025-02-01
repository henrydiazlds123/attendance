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

@bp.route('/attendance/report') #old
@role_required('Admin', 'Owner', 'User')
def attendance_report():
    # Obtener año y mes actuales
    current_year = datetime.now().year
    current_month = datetime.now().month
    # Obtener años únicos de la base de datos
    available_years = db.session.query(func.extract('year', Attendance.sunday_date)).distinct().order_by(func.extract('year', Attendance.sunday_date)).all()
    available_years = [y[0] for y in available_years]

    # Obtener meses únicos de la base de datos
    available_months = db.session.query(func.extract('month', Attendance.sunday_date)).distinct().order_by(func.extract('month', Attendance.sunday_date)).all()
    available_months = [m[0] for m in available_months]
    
    # Convertir los meses a nombres abreviados y traducirlos
    month_names = [{"num": m, "name": _(datetime(2000, m, 1).strftime('%b'))} for m in available_months]  # Translate month names
  

    # Determinar valores predeterminados
    current_year  = datetime.now().year
    default_year  = available_years[0] if len(available_years) == 1 else current_year
    default_month = available_months[0] if len(available_months) == 1 else None
    # Obtener los valores de los filtros desde los parámetros de la URL
    selected_year = request.args.get('year', type=int, default=current_year)
    selected_month = request.args.get('month', type=int, default=current_month)

    # Obtener los domingos sin filtrar por mes o año
    sundays = db.session.query(Attendance.sunday_date).filter(
        Attendance.meeting_center_id == session['meeting_center_id']  # Filtro por meeting center
    ).distinct().order_by(Attendance.sunday_date).all()
    # Consulta base con filtro de año obligatorio
    query = db.session.query(Attendance.sunday_date).filter(
        Attendance.meeting_center_id == session['meeting_center_id']
    )
    if selected_year:
        query = query.filter(extract('year', Attendance.sunday_date) == selected_year)
        

    # Seleccionar las primeras 5 fechas de domingo, si hay menos de 5 mostrar todas
    sunday_dates = [s[0] for s in sundays[:5]] if len(sundays) > 5 else [s[0] for s in sundays]
    
    if selected_month:
        query = query.filter(extract('month', Attendance.sunday_date) == selected_month)

    # Obtener registros de asistencia con el filtro por meeting center
    attendance_records = Attendance.query.filter(Attendance.sunday_date.in_(sunday_dates), Attendance.meeting_center_id == session['meeting_center_id']  # Filtro por meeting center
    ).order_by(Attendance.student_name, Attendance.sunday_date).all()
    
    
    sundays = query.distinct().order_by(Attendance.sunday_date).all()
    sunday_dates = [s[0] for s in sundays]

    # Obtener registros de asistencia
    attendance_query = Attendance.query.filter(
        Attendance.meeting_center_id == session['meeting_center_id']
    )
    if selected_year:
        attendance_query = attendance_query.filter(extract('year', Attendance.sunday_date) == selected_year)
        
    if selected_month:
        attendance_query = attendance_query.filter(extract('month', Attendance.sunday_date) == selected_month)
        
    attendance_records = attendance_query.order_by(Attendance.student_name, Attendance.sunday_date).all()
    # Construcción del diccionario de asistencia
    students = {}
    
    for record in attendance_records:
        if record.student_name not in students:
            students[record.student_name] = {date: False for date in sunday_dates}
        students[record.student_name][record.sunday_date] = True
        

    return render_template(
        'attendance_report.html',
        students=students,
        dates=sunday_dates,
        available_years=available_years,
        available_months=month_names,  # Opción de meses
        disable_month=len(available_months) == 1,  # Deshabilitar el select si hay un solo mes
        selected_year=selected_year,
        selected_month=selected_month,
        meeting_center_name=session.get('meeting_center_name', ''),
    )