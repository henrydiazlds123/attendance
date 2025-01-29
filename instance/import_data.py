import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import db, Attendance  # Importa el modelo y la configuración de tu base de datos
import os

def import_attendance_data():
    """Limpia la tabla de Attendance y luego importa datos del archivo attendance.csv."""
    # Configura la conexión con la base de datos
    DATABASE_URI = 'sqlite:///attendance.db'  # Ajusta según tu base de datos
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Elimina todos los registros existentes
    session.query(Attendance).delete()
    session.commit()
    print("Todos los registros existentes en la tabla 'attendance' fueron eliminados.")

    # Define la ruta del archivo 'attendance.csv' en el mismo directorio
    file_path = os.path.join(os.path.dirname(DATABASE_URI.replace('sqlite:///', '')), 'attendance.csv')

    # Verifica que el archivo existe
    if not os.path.isfile(file_path):
        print(f"No se encontró el archivo: {file_path}")
        return

    # Carga los datos desde el archivo CSV
    data = pd.read_csv(file_path, encoding='latin1')

    # Inserta los datos en la tabla
    records = []
    for _, row in data.iterrows():
        attendance_record = Attendance(
            id=row['id'],
            student_name=row['student_name'],
            class_id=row['class_id'],
            class_code=row['class_code'],
            sunday_date=pd.to_datetime(row['sunday_date']).date(),
            sunday_code=row['sunday_code'],
            submit_date=pd.to_datetime(row['submit_date']),
            meeting_center_id=row['meeting_center_id']
        )
        records.append(attendance_record)
    
    session.bulk_save_objects(records)
    session.commit()
    print("Los datos fueron importados exitosamente.")

if __name__ == "__main__":
    import_attendance_data()
