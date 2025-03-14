# app/utils.py
import os
import re
import time
import pandas as pd
import requests
import logging
import unicodedata
from   sqlalchemy   import func
from   app.config   import Config
from   functools    import wraps
from   flask_babel  import format_date, gettext as _
from   datetime     import date, datetime, timedelta
from   app.models   import Attendance, Classes, db, Setup, Member
from   flask        import current_app, flash, logging, redirect, session, url_for, request, g


# ================================================================
def role_required(*roles):
    """Decorador para restringir el acceso basado en roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.user is None:  # Si no está autenticado, lo redirigimos a login
                return redirect(url_for('auth.login', next=request.url))
            
            user_role = session.get('role')  # Suponiendo que el rol se almacena en la sesión
            if user_role not in roles:
                flash(_('You do not have permission to perform this action.'), 'danger')
                return redirect(url_for('auth.login'))  # O podrías redirigir a otra página
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ================================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:  # Si el usuario no está autenticado
            next_url = request.url  # Guardamos la URL a la que intentaba acceder
            return redirect(url_for('auth.login', next=next_url))  # Pasamos 'next' como parámetro
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
        # Buscar el valor de SelectedMeetingCenterId desde la tabla Setup
        setup = Setup.query.filter_by(key='SelectedMeetingCenterId', meeting_center_id=1).first()
        if setup:
            return setup.value  # Retorna el valor del meeting_center_id almacenado en Setup
        return 'all'  # Si no hay valor en Setup, por defecto retorna 'all'
    return session.get('meeting_center_id')  # Para otros roles, usar el valor de la sesión


# ================================================================
def get_attendance_by_class_data():
    # Obtener los datos de asistencia agrupados por clase
    attendance_by_class = db.session.query(
        Attendance.class_id,
        func.count(Attendance.student_name.distinct()).label('attendance_count')
    ).join(Classes).filter(Classes.class_type == 'Main').group_by(Attendance.class_id).all()

    return attendance_by_class


# ================================================================
def translations():
    main_organizations = [
        {'id': 1, 'name': _('Bishopric')},
        {'id': 2, 'name': _('Elders Quorum')},
        {'id': 3, 'name': _('Relief Society')},
        {'id': 4, 'name': _('Aaronic Priesthood Quorums')},
        {'id': 5, 'name': _('Young Women')},
        {'id': 6, 'name': _('Sunday School')},
        {'id': 7, 'name': _('Primary')},
        {'id': 8, 'name': _('Other')}
    ]

    
# ================================================================
def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return ''.join([c for c in nfkd_form if not unicodedata.combining(c) or c == 'ñ' or c == 'Ñ'])


# ================================================================
def get_last_sunday():
    """Sets default sunday_date to last Sunday if today is not Sunday, otherwise uses today."""
    today = datetime.now().date()
    days_since_sunday = today.weekday()  # 0 = Monday, 6 = Sunday
    last_sunday       = today - timedelta(days=days_since_sunday + 1) if today.weekday() != 6 else today
    return last_sunday.strftime('%Y-%m-%d')


# =================================================================
def get_age(birth_date):
    """Calcula la edad a partir de la fecha de nacimiento."""
    if birth_date:
        today = datetime.now().date()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return 0


# =================================================================
def get_category(age):
    """Asigna una categoría a la edad."""
    if age < 12:
        return _('Children')
    elif age > 11 and age < 18:  # Cambié para que cubra el rango de 12 a 17 para Jóvenes
        return _('Youth')
    elif age > 18 and age < 36:  # Cambié para que cubra el rango de 12 a 17 para Jóvenes
        return _('Youth Adult')
    else:
        return _('Adult')


# =================================================================
def get_category_filter(category):
    if category == _('Children'):
        return Member.birth_date >= date(date.today().year - 11, 1, 1)
    elif category == _('Youth'):
        return (Member.birth_date < date(date.today().year - 11, 1, 1)) & (Member.birth_date >= date(date.today().year - 17, 1, 1))
    elif category == _('Young single adult'):
        return (Member.birth_date < date(date.today().year - 18, 1, 1)) & \
               (Member.birth_date >= date(date.today().year - 36, 1, 1)) & \
               (Member.marital_status == 'Single')
    elif category == _('Adult'):
        return Member.birth_date < date(date.today().year - 17, 1, 1)
    return None


# =================================================================
def get_years_in_unit(arrival_date):
    """Calcula los años en la unidad desde la fecha de llegada."""
    if arrival_date:
        today = datetime.now().date()  # Llamar a datetime.date.today()
        years = today.year - arrival_date.year
        # Compara meses y días para asegurar que no se cuenta un año incompleto
        if today.month < arrival_date.month or (today.month == arrival_date.month and today.day < arrival_date.day):
            years -= 1
        return years
    return 0


# =================================================================
def validate_import_data(df):
    errors = []

    for index, row in df.iterrows():
        if not isinstance(row["full_name"], str) or row["full_name"].strip() == "":
            errors.append(f"Row {index+1}: Full name is required.")

        if not isinstance(row["birth_date"], str) or not re.match(r"\d{4}-\d{2}-\d{2}", row["birth_date"]):
            errors.append(f"Row {index+1}: Invalid birth date format (YYYY-MM-DD expected).")

        if row["gender"] not in ["M", "F"]:
            errors.append(f"Row {index+1}: Gender must be 'M' or 'F'.")

        if not isinstance(row["family_head"], str) or row["family_head"].strip() == "":
            errors.append(f"Row {index+1}: Family Head is required.")

    return errors


# =================================================================
def convertir_texto_a_fecha(txt_fecha):
    get_months = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Ago": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dic": 12,
        "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
        "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
    }

    if not txt_fecha or not isinstance(txt_fecha, str):
        return None

    part = txt_fecha.replace("-", " ").split()

    if len(part) not in [3, 4]:
        return None  # Formato inválido

    try:
        day = int(part[0])
        month = part[1].lower()
        year = int(part[-1])

        if len(str(year)) == 2:  # Manejo de años cortos
            year += 2000

        if month in get_months:
            month = get_months[month]
        else:
            return None  # Mes inválido

        return datetime(year, month, day).date()
    except (ValueError, KeyError):
        return None


# =================================================================
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
def get_coordinates(address, city, retries=3, delay=1):
    query = f"{address}, {city}"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={query}&key={GOOGLE_MAPS_API_KEY}"
    
    for _ in range(retries):
        try:
            response = requests.get(url).json()
            if response["status"] == "OK":
                location = response["results"][0]
                return (
                    location["geometry"]["location"]["lat"],
                    location["geometry"]["location"]["lng"],
                    location["formatted_address"]
                )
            elif response["status"] == "OVER_QUERY_LIMIT":
                time.sleep(delay)
            else:
                break
        except Exception as e:
            logging.error(f"Error al obtener coordenadas: {str(e)}")
            break
    return None, None, None


# =================================================================
def get_valid_value(value):
    if isinstance(value, float) and pd.isna(value):  # Verifica si es NaN de Pandas
        return None
    value = str(value).strip()  # Convierte a string y elimina espacios
    return None if value.lower() in ["nan", "none", "null", ""] else value


# =================================================================
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in ALLOWED_EXTENSIONS


# =================================================================
def process_import(df, mappings, meeting_center_id):
    print("Mapeo de columnas Antes:", mappings)  # Verifica el mapeo antes de procesar
    updated = 0
    added = 0
    existing_members = {(m.full_name, m.birth_date): m for m in Member.query.all()}

    for _, row in df.iterrows():
        try:
            print(f"Procesando fila: {row.to_dict()}")  # 🔹 Agregar dentro del bucle

            full_name         = get_valid_value(row.get('full_name', ''))
            birth_date        = convertir_texto_a_fecha(row.get('birth_date', ''))
            gender            = get_valid_value(row.get('gender', ''))
            marital_status    = get_valid_value(row.get('marital_status', ''))
            address           = get_valid_value(row.get('address', ''))
            city              = get_valid_value(row.get('city', ''))
            state             = get_valid_value(row.get('state', ''))
            zip_code          = get_valid_value(row.get('zip_code', ''))
            priesthood        = get_valid_value(row.get('priesthood', ''))
            priesthood_office = get_valid_value(row.get('priesthood_office', ''))
            calling           = get_valid_value(row.get('calling', ''))
            arrival_date      = convertir_texto_a_fecha(row.get('arrival_date', ''))
            family_head       = get_valid_value(row.get('family_head', ''))
            print(f"Full Name: {full_name}")
            print(f"Birth Date: {birth_date}")
            print(f"Gender: {gender}")
            print(f"Marital Status: {marital_status}")
            print(f"Address: {address}")
            print(f"City: {city}")
            print(f"State: {state}")
            print(f"Zip Code: {zip_code}")
            print(f"Priesthood: {priesthood}")
            print(f"Priesthood Office: {priesthood_office}")
            print(f"Calling: {calling}")
            print(f"Arrival Date: {arrival_date}")
            print(f"Family Head: {family_head}")
            # Separar nombres
            name_parts = full_name.split(',')
            last_name  = name_parts[0].strip().split()[0]
            first_name = name_parts[1].strip().split()[0]

            if not full_name or not birth_date:
                continue

            if (full_name, birth_date) in existing_members:
                member = existing_members[(full_name, birth_date)]
                member.marital_status    = marital_status
                member.address           = address
                member.city              = city
                member.state             = state
                member.zip_code          = zip_code
                member.priesthood        = priesthood
                member.priesthood_office = priesthood_office
                member.calling           = calling
                member.arrival_date      = arrival_date
                member.family_head       = family_head
                member.meeting_center_id = meeting_center_id
                updated += 1
            else:
                new_member = Member(
                    full_name         = full_name,
                    preferred_name    = f"{first_name} {last_name}",
                    short_name        = f"{last_name}, {first_name}",
                    birth_date        = birth_date,
                    gender            = gender,
                    marital_status    = marital_status,
                    address           = address,
                    city              = city,
                    state             = state,
                    zip_code          = zip_code,
                    priesthood        = priesthood,
                    priesthood_office = priesthood_office,
                    calling           = calling,
                    arrival_date      = arrival_date,
                    family_head       = family_head,
                    meeting_center_id = meeting_center_id,
                )
                db.session.add(new_member)
                added += 1
        except Exception as e:
            current_app.logger.error(f"Error procesando fila: {str(e)}")

    try:
        db.session.commit()
        print("🚀 Transacción completada con éxito.")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Error al guardar en la base de datos: {str(e)}")

    return added, updated  # ✅ Agregar retorno al final