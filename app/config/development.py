import os
from .base import BaseConfig

class DevelopmentConfig(BaseConfig):
    DEBUG                   = True
    ENV                     = "development"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BaseConfig.BASE_DIR, 'instance', 'attendance_dev.db')}"
    BASE_URL                = "http://127.0.0.1:5000"
