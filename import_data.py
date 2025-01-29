import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Attendance  # Asegúrate de que Attendance está importado correctamente
import os

def import_attendance_data():
    """Limpia la tabla de Attendance y luego importa datos desde el archivo attendance.csv."""
    # Configura la conexión con la base de datos
    DATABASE_URI = 'sqlite:///attendance.db'  # Ajusta si usas otra base de datos
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

    try:
        # Carga los datos desde el archivo CSV (tab-delimited)
        data = pd.read_csv(file_path, encoding='utf-16', sep="\t")
    except Exception as e:
        print(f"Error al leer el archivo CSV: {e}")
        return

    # Inserta los datos en la tabla
    records = []
    for _, row in data.iterrows():
        try:
            attendance_record = Attendance(
                student_name=row['student_name'],
                class_id=row['class_id'],
                class_code=row['class_code'],
                sunday_date=pd.to_datetime(row['sunday_date']).date(),
                sunday_code=row['sunday_code'],
                submit_date=pd.to_datetime(row['submit_date']),
                meeting_center_id=row['meeting_center_id']
            )
            records.append(attendance_record)
        except Exception as e:
            print(f"Error al procesar fila {row.to_dict()}: {e}")

    try:
        session.bulk_save_objects(records)
        session.commit()
        print(f"{len(records)} registros fueron importados exitosamente.")
    except Exception as e:
        print(f"Error al guardar los datos en la base de datos: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    import_attendance_data()
