import os
import io
import csv
from functools    import wraps
from datetime     import datetime, timedelta
from flask        import flash, redirect, session, url_for, request, Response, g
from flask_babel  import format_date, gettext as _
from config       import Config
from models import Attendance, Classes, db
from sqlalchemy import func



# ================================================================
def role_required(*roles):
    """Decorador para restringir el acceso basado en roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get('role')  # Suponiendo que el rol se almacena en la sesión
            if user_role not in roles:
                flash(_('You do not have permission to perform this action.'), 'danger')
                return redirect(url_for('routes.login'))  # Ajusta la ruta de redirección según sea necesario
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ================================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('routes.login', next=request.url))  # Redirige a login si no hay usuario
        return f(*args, **kwargs)
    return decorated_function


# ================================================================
def get_current_time(timezone='America/Denver'):
    import pytz
    from datetime import datetime
    tz = pytz.timezone(timezone)
    return datetime.now(tz)


# ================================================================
def get_next_sunday():
    """Devuelve la fecha del próximo domingo, formateada según el locale. Si hoy es domingo, devuelve la fecha de hoy."""
    today = datetime.now().date()
    
    # Si hoy es domingo
    if today.weekday() == 6:  # 6 es domingo
        return today  # Formatear la fecha actual según el locale
    else:
        # Calcular cuántos días faltan para el siguiente domingo
        days_until_sunday = 6 - today.weekday()
        next_sunday = today + timedelta(days=days_until_sunday)
        print(format_date(next_sunday) )
        return next_sunday  # Formatear la fecha del siguiente domingo


# ================================================================
def get_sunday_week(fecha):
    """Determina la semana del mes para una fecha dada."""
    return (fecha.day - 1) // 7 + 1


# ================================================================
def get_next_sunday_code(next_sunday):
    start_of_year    = datetime(next_sunday.year, 1, 1).date()
    days_since_start = (next_sunday - start_of_year).days
    sunday_code      = (days_since_start * 73 + 42) % 10000
    return sunday_code


# ================================================================
def clean_qr_folder(folder_path):
    """Elimina todos los archivos en la carpeta especificada."""
    if os.path.exists(folder_path):
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)  # Elimina el archivo
            except Exception as e:
                print(f"Error al eliminar {file_path}: {e}")


# ================================================================
def clean_qr_images(folder_path):
    for file in os.listdir(folder_path):
        if file.endswith(".png"):
            os.remove(os.path.join(folder_path, file))


# ================================================================
@staticmethod
def get_output_dir():
    """Obtiene el directorio de salida dinámico basado en el número de unidad."""
    unit_number = session.get('meeting_center_number', 'default')  # Usa 'default' si no hay sesión activa
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qr_codes', str(unit_number))


# ================================================================
def format_date_custom(date_obj, locale=None):
    """
    Formats a date object based on the locale.
    :param date_obj: The date object to format.
    :param locale: The locale to use for formatting.
    :return: A formatted date string.
    """
    # Default to application-wide locale if not provided
    if not locale:
        locale = get_locale()
    return format_date(date_obj, format='long', locale=locale)


# ================================================================
def get_locale():
    lang = request.cookies.get('lang')  # Example: Retrieve from cookie
    if lang in Config.LANGUAGES:
        return lang
    return request.accept_languages.best_match(Config.LANGUAGES)


# ================================================================
def get_months():
    return [
        ('1', _('Jan')), 
        ('2', _('Feb')), 
        ('3', _('Mar')), 
        ('4', _('Apr')), 
        ('5', _('May')), 
        ('6', _('Jun')), 
        ('7', _('Jul')), 
        ('8', _('Aug')), 
        ('9', _('Sep')), 
        ('10', _('Oct')), 
        ('11', _('Nov')), 
        ('12', _('Dec'))
    ]


# ================================================================
def get_meeting_center_id():
    """Obtiene el meeting_center_id basado en el rol y la sesión."""
    if session.get('role') == 'Owner':
        return session.get('meeting_center_id', 'all')  # 'all' si no está definido
    return session.get('meeting_center_id')  # Para otros roles



# GRFICOS
def get_attendance_by_class_data():
    # Obtener los datos de asistencia agrupados por clase
    attendance_by_class = db.session.query(
        Attendance.class_id,
        func.count(Attendance.student_name.distinct()).label('attendance_count')
    ).join(Classes).filter(Classes.class_type == 'Main').group_by(Attendance.class_id).all()

    # Aquí puedes agregar la lógica para obtener el nombre de la clase a partir de class_id
    # Por ejemplo, con una consulta adicional o utilizando la relación con la tabla Classes
    return attendance_by_class


import plotly.express as px

def plot_attendance_by_class(attendance_data):
    classes = [f"Clase {class_id}" for class_id, _ in attendance_data]  # Puedes mejorar esto con nombres reales de clases
    attendance_counts = [attendance_count for _, attendance_count in attendance_data]

    fig = px.bar(
        x=classes, 
        y=attendance_counts, 
        labels={'x': 'Clase', 'y': 'Estudiantes Asistentes'}, 
        title="Asistencia por Clase"
    )
    return fig.to_html(full_html=False)
