from app import create_app  # Importa tu app y la instancia de la base de datos
from models import Organization, Classes  # Importa los modelos

def extract_db_values():
    # Crear una lista para almacenar las cadenas traducibles
    translatable_strings = []

    # Extraer valores del modelo Organization
    organizations = Organization.query.all()
    print(f"Found {len(organizations)} organizations.")  # Depura el número de organizaciones
    for org in organizations:
        if hasattr(org, 'name') and org.name:  # Asegúrate de que 'name' no esté vacío
            print(f"Adding organization name: {org.name}")  # Depura los nombres de las organizaciones
            translatable_strings.append(org.name)

    # Extraer valores del modelo Classes
    classes = Classes.query.all()
    print(f"Found {len(classes)} classes.")  # Depura el número de clases
    for cls in classes:
        if hasattr(cls, 'class_name') and cls.class_name:  # Verifica que 'class_name' no esté vacío
            print(f"Adding class name: {cls.class_name}")  # Depura los nombres de las clases
            translatable_strings.append(cls.class_name)
        if hasattr(cls, 'short_name') and cls.short_name:  # Verifica que 'short_name' no esté vacío
            print(f"Adding short name: {cls.short_name}")  # Depura los short names
            translatable_strings.append(cls.short_name)

    # Crear el archivo translations.py con las cadenas traducibles
    with open('translations.py', 'w') as f:
        f.write("# Generated translatable strings\n")
        for value in set(translatable_strings):  # Usar `set` para evitar duplicados
            f.write(f"_('{value}')\n")  # Escribe las cadenas sin envolverlas en gettext
            print(f"Writing translation for: {value}")  # Depura el proceso de escritura

if __name__ == "__main__":
    app = create_app()  # Usa la fábrica de aplicaciones para crear la app
    with app.app_context():  # Necesario para que Flask-Babel funcione correctamente
        with app.test_request_context():  # Agregar un contexto de solicitud para evitar el error
            extract_db_values()
