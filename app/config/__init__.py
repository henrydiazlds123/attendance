#app/config/__init__.py
import os
from .development import DevelopmentConfig
from .production import ProductionConfig

configurations = {
    "development": DevelopmentConfig,
    "production": ProductionConfig
}

env = os.getenv("FLASK_ENV", "development")
Config = configurations.get(env, DevelopmentConfig)  # Usa desarrollo como predeterminado
