from app.utils    import *
from sqlalchemy   import func
from datetime     import datetime
from flask_babel  import gettext as _
from collections  import defaultdict
from app.models   import db, Classes, Attendance
from flask        import Blueprint, jsonify, render_template, request

bp_stats = Blueprint('stats', __name__)

# =============================================================================================
@bp_stats.route('/')
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
    return render_template('stats/stats.html',
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
@bp_stats.route("/classes/data")
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
@bp_stats.route("/classes/percentage_data")
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
@bp_stats.route('/stats2/')
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