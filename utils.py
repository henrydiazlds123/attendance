import os
import io
import csv
from functools    import wraps
from datetime     import datetime, timedelta
from flask        import flash, redirect, session, url_for, request, Response
from flask_babel  import format_date, gettext as _
from config       import Config
from itsdangerous import URLSafeTimedSerializer
from models       import Attendance




def role_required(*roles):
    """Decorador para restringir el acceso basado en roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get('role')  # Suponiendo que el rol se almacena en la sesión
            if user_role not in roles:
                flash('You do not have permission to perform this action.', 'danger')
                return redirect(url_for('routes.login'))  # Ajusta la ruta de redirección según sea necesario
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_time(timezone='America/Denver'):
    import pytz
    from datetime import datetime
    tz = pytz.timezone(timezone)
    return datetime.now(tz)


# def get_next_sunday():
#     """Devuelve la fecha del próximo domingo. Si hoy es domingo, devuelve la fecha de hoy."""
#     today = datetime.now().date()
#     if today.weekday() == 6:  # 6 es domingo
#         return format_datetime(today)
#     else:
#         days_until_sunday = 6 - today.weekday()
#         return today + timedelta(days=days_until_sunday)
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


def get_sunday_week(fecha):
    """Determina la semana del mes para una fecha dada."""
    return (fecha.day - 1) // 7 + 1


def get_next_sunday_code(next_sunday):
    start_of_year    = datetime(next_sunday.year, 1, 1).date()
    days_since_start = (next_sunday - start_of_year).days
    sunday_code      = (days_since_start * 73 + 42) % 10000
    return sunday_code


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


def clean_qr_images(folder_path):
    for file in os.listdir(folder_path):
        if file.endswith(".png"):
            os.remove(os.path.join(folder_path, file))


@staticmethod
def get_output_dir():
    """Obtiene el directorio de salida dinámico basado en el número de unidad."""
    unit_number = session.get('meeting_center_number', 'default')  # Usa 'default' si no hay sesión activa
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qr_codes', str(unit_number))

# Generate token for user
def generate_token(user_id):
    serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
    return serializer.dumps(user_id, salt='login-salt')


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

def get_locale():
    lang = request.cookies.get('lang')  # Example: Retrieve from cookie
    if lang in Config.LANGUAGES:
        return lang
    return request.accept_languages.best_match(Config.LANGUAGES)


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

from flask import request, Response
import csv
from datetime import datetime
import io  # Importar io para usar StringIO

def export_attendance_to_csv():
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
