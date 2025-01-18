from functools import wraps
import os
import re
from datetime import datetime, timedelta

from flask import flash, redirect, session, url_for



def is_admin_or_owner():
    role = session.get('role')
    if role not in ['Owner', 'Admin']:
        flash('You do not have permission to perform this action.', 'danger')
        return False
    return True


def is_owner():
    role = session.get('role')
    if role not in ['Owner']:
        flash('You do not have permission to perform this action.', 'danger')
        return False
    return True



def role_required(*roles):
    """Decorador para restringir el acceso basado en roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get('role')  # Suponiendo que el rol se almacena en la sesión
            if user_role not in roles:
                flash('No tiene permisos para acceder a esta página.')
                return redirect(url_for('routes.login'))  # Ajusta la ruta de redirección según sea necesario
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_time(timezone='America/Denver'):
    import pytz
    from datetime import datetime
    tz = pytz.timezone(timezone)
    return datetime.now(tz)


def get_next_sunday():
    """Devuelve la fecha del próximo domingo. Si hoy es domingo, devuelve la fecha de hoy."""
    today = datetime.now().date()
    if today.weekday() == 6:  # 6 es domingo
        return today
    else:
        days_until_sunday = 6 - today.weekday()
        return today + timedelta(days=days_until_sunday)


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

