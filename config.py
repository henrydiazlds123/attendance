import os
from datetime import datetime
import pytz

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', '2435e1ab4b6789d8b1a8c3374db0470c')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///attendance.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    
    # BASE_URL configuration
    #BASE_URL  = "https://attendance.indicegenealogico.com" #Production
    BASE_URL = "http://127.0.0.1:5000" #local

    # Output directory for QR codes
    # OUTPUT_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qr_codes') #Production
    MOUNTAIN_TZ   = pytz.timezone("America/Denver") # Define Mountain Time Zone
    MOUNTAIN_TIME = datetime.now(MOUNTAIN_TZ) # Get the current time in Mountain Time
    CURRENT_DATE  = MOUNTAIN_TIME.date() # Use mountain_time.date() to get the date part
