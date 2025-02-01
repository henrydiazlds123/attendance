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


@bp.route('/attendance/report')
def attendance_report():
    # Obtener años únicos de la base de datos
    available_years = db.session.query(func.extract('year', Attendance.sunday_date)).distinct().order_by(func.extract('year', Attendance.sunday_date)).all()
    available_years = [y[0] for y in available_years]

    # Obtener meses únicos de la base de datos
    available_months = db.session.query(func.extract('month', Attendance.sunday_date)).distinct().order_by(func.extract('month', Attendance.sunday_date)).all()
    available_months = [m[0] for m in available_months]

    # Convertir los meses a nombres abreviados y traducirlos
    month_names = [{"num": m, "name": _(datetime(2000, m, 1).strftime('%b'))} for m in available_months]

    # Obtener los valores de los filtros desde los parámetros de la URL
    selected_year = request.args.get('year', type=int)
    selected_month = request.args.get('month', type=int)

    # Consulta base con filtro de año obligatorio
    query = db.session.query(Attendance.sunday_date).filter(
        Attendance.meeting_center_id == session['meeting_center_id']
    )

    if selected_year:
        query = query.filter(extract('year', Attendance.sunday_date) == selected_year)

    if selected_month:
        query = query.filter(extract('month', Attendance.sunday_date) == selected_month)

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
        available_months=month_names,
        selected_year=selected_year,
        selected_month=selected_month,
        meeting_center_name=session.get('meeting_center_name', ''),
        disable_month=len(available_months) == 1
    )