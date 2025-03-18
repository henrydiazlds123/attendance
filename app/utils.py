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
from   flask        import flash, logging, redirect, session, url_for, request, g


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

    callings = [
        { _('Assistant Ward Mission Leader')},
        { _('Bishop')},
        { _('Bishopric First Counselor')},
        { _('Bishopric Second Counselor')},
        { _('Communication Specialist')},
        { _('Deacons Quorum Adviser')},
        { _('Deacons Quorum President')},
        { _('Elders Quorum First Counselor')},
        { _('Elders Quorum President')},
        { _('Elders Quorum Second Counselor')},
        { _('Elders Quorum Secretary')},
        { _('Elders Quorum Teacher')},
        { _('Nursery Leader')},
        { _('Priests Quorum Adviser')},
        { _('Priests Quorum First Assistant')},
        { _('Priests Quorum Second Assistant')},
        { _('Priests Quorum Secretary')},
        { _('Primary Activities Leader')},
        { _('Primary First Counselor')},
        { _('Primary Music Leader')},
        { _('Primary President')},
        { _('Primary Second Counselor')},
        { _('Primary Secretary')},
        { _('Primary Teacher')},
        { _('Relief Society Activity Coordinator')},
        { _('Relief Society First Counselor')},
        { _('Relief Society Ministering Secretary')},
        { _('Relief Society President')},
        { _('Relief Society Second Counselor')},
        { _('Relief Society Service Coordinator')},
        { _('Relief Society Teacher')},
        { _('Scheduler--Building 1')},
        { _('Stake Assistant Clerk--Membership')},
        { _('Stake Young Women Second Counselor')},
        { _('Sunday School First Counselor')},
        { _('Sunday School President')},
        { _('Sunday School Second Counselor')},
        { _('Sunday School Secretary')},
        { _('Sunday School Teacher')},
        { _('Teachers Quorum Adviser')},
        { _('Teachers Quorum First Counselor')},
        { _('Teachers Quorum President')},
        { _('Teachers Quorum Second Counselor')},
        { _('Ward Assistant Clerk--Finance')},
        { _('Ward Assistant Clerk--Membership')},
        { _('Ward Assistant Executive Secretary')},
        { _('Ward Clerk')},
        { _('Ward Executive Secretary')},
        { _('Ward Mission Leader')},
        { _('Ward Missionary')},
        { _('Ward Temple and Family History Consultant')},
        { _('Ward Temple and Family History Leader')},
        { _('Ward/Branch Interpreter')},
        { _('Welfare and Self-Reliance Specialist')},
        { _('Young Women Class Adviser')},
        { _('Young Women Class First Counselor')},
        { _('Young Women Class President')},
        { _('Young Women Class Second Counselor')},
        { _('Young Women First Counselor')},
        { _('Young Women President')},
        { _('Young Women Second Counselor')},
        { _('Young Women Specialist - Sports')}
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
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }
    
    #print(f"Fecha recibida: {txt_fecha}")
    if not txt_fecha:
        return None
    
    # Si ya es un objeto date, devolverlo directamente
    if isinstance(txt_fecha, date):
        return txt_fecha

    # Caso 1: Manejar formato MM/DD/YYYY
    if "/" in txt_fecha:
        try:
            fecha_convertida = datetime.strptime(txt_fecha, "%m/%d/%Y").date()
            #print(f"Fecha convertida (MM/DD/YYYY): {fecha_convertida}")
            return fecha_convertida
        except ValueError:
            #print("Error: Formato inválido para MM/DD/YYYY")
            return None

    # Caso 2: Manejar formato DD MMM YYYY
    part = txt_fecha.replace("-", " ").split()
    if len(part) not in [3, 4]:  
        #print(f"Error: Formato inválido con {len(part)} partes")
        return None  

    try:
        day = int(part[0])
        month = part[1].lower()
        year = int(part[-1])

        if len(str(year)) == 2:  
            year += 2000

        if month in get_months:
            month = get_months[month]
        else:
            #print(f"Error: Mes inválido '{month}'")
            return None  

        fecha_convertida = date(year, month, day)
        #print(f"Fecha convertida (DD MMM YYYY): {fecha_convertida}")
        return fecha_convertida

    except (ValueError, KeyError) as e:
        #print(f"Error al convertir la fecha: {e}")
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
permanently_excluded_fields = ['gender', 'birth_date', 'fixed_address', 'lat', 'lon', 'preferred_name', 'short_name']

def process_import(df, column_mapping, meeting_center_id):
    """
    Procesa la importación de datos de miembros desde un DataFrame.
    """
    # Renombrar las columnas del DataFrame según column_mapping
    df = df.rename(columns={v: k for k, v in column_mapping.items() if v in df.columns})

    # Limpiar posibles espacios en blanco adicionales en los nombres de las columnas
    df.columns = df.columns.str.strip()

    # Convertir arrival_date y birth_date usando la función convertir_texto_a_fecha
    if 'arrival_date' in df.columns:
        df['arrival_date'] = df['arrival_date'].apply(convertir_texto_a_fecha)
    if 'birth_date' in df.columns:
        df['birth_date'] = df['birth_date'].apply(convertir_texto_a_fecha)

    # Asegurarnos de que la columna 'gender' no contenga valores vacíos o NaN
    if df['gender'].isna().any():
        print("Advertencia: Algunas filas tienen 'gender' como NaN. Revise los datos de entrada.")
        df = df.dropna(subset=['gender'])  # Elimina las filas con 'gender' vacío

    added = 0
    updated = 0

    # Obtenemos los miembros actuales en la base de datos para este centro de reunión
    miembros_existentes = Member.query.filter_by(meeting_center_id=meeting_center_id).all()

    # Creamos un set de los nombres completos (full_name) de los registros CSV
    full_names_csv = {row['full_name'] for _, row in df.iterrows()}

    # Iteramos sobre los miembros existentes en la base de datos
    for miembro in miembros_existentes:
        # Si el miembro no está en el archivo CSV (basado en el nombre completo)
        if miembro.full_name not in full_names_csv:
            # Actualizamos los campos moved_out y excluded
            miembro.moved_out = True
            miembro.excluded = True
            db.session.add(miembro)  # Añadimos el cambio a la sesión
            # updated += 1
        else:
            # Si está en el archivo CSV, actualizamos moved_out y excluded a False
            miembro.moved_out = False
            miembro.excluded = False
            db.session.add(miembro)  # Añadimos el cambio a la sesión
            # updated += 1

    # Ahora procesamos los registros del CSV
    for _, row in df.iterrows():
        # Verificar que 'full_name' y 'gender' no sean nulos
        if pd.isna(row['full_name']):
            print(f"Error: Fila sin 'full_name' válido. Saltando fila...")
            continue  # Saltar filas sin 'full_name'

        if pd.isna(row['gender']):
            print(f"Advertencia: Fila con 'gender' nulo. Saltando fila...")
            continue  # Saltar filas con 'gender' vacío

        # Buscar si el miembro ya existe
        member = Member.query.filter_by(full_name=row['full_name'], meeting_center_id=meeting_center_id).first()

        if member:
            # Si existe, actualizamos los campos
            for field in column_mapping:
                if field in row and not pd.isna(row[field]):
                    setattr(member, field, row[field])
            updated += 1
        else:
            # Si no existe, crear un nuevo miembro
            # Aquí, excluimos 'full_name' de los campos que vamos a pasar al crear el miembro
            member_data = {field: row[field] for field in column_mapping if field in row and not pd.isna(row[field])}
            member_data['full_name'] = row['full_name']  # Aseguramos que 'full_name' esté explicitamente presente
            new_member = Member(
                meeting_center_id=meeting_center_id,
                **member_data  # Usamos ** para pasar los campos de manera correcta
            )
            db.session.add(new_member)
            added += 1

    # Commit a la base de datos
    db.session.commit()
    print("🚀 Transacción completada con éxito.")

    return added, updated
