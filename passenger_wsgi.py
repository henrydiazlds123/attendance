import sys
import os

# Agregar la ruta del proyecto al sys.path
sys.path.insert(0, os.path.dirname(__file__))

from app import app as application  # Importa la instancia de Flask