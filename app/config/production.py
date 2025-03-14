import os
from .base import BaseConfig

class ProductionConfig(BaseConfig):
    DEBUG                   = False
    ENV                     = "production"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BaseConfig.BASE_DIR, 'instance', 'attendance.db')}")
    BASE_URL                = "https://attendance.indicegenealogico.com"
