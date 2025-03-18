import os
import pytz
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()


class BaseConfig:
    BASE_DIR                       = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # Directorio raíz del proyecto
    SECRET_KEY                     = os.getenv('SECRET_KEY', 'default-secret-key')
    MOUNTAIN_TZ                    = pytz.timezone("America/Denver")  # Define Mountain Time Zone
    MOUNTAIN_TIME                  = datetime.now(MOUNTAIN_TZ)  # Get the current time in Mountain Time
    CURRENT_DATE                   = MOUNTAIN_TIME.date()  # Solo la fecha
    LANGUAGES                      = ['en', 'es', 'pt']
    SESSION_PERMANENT              = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_MAPS_API_KEY            = os.getenv('GOOGLE_MAPS_API_KEY', 'default-google-key')
