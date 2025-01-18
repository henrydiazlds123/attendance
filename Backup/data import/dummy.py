from models import db, User, Attendance, Config, MeetingCenter, Classes
from werkzeug.security import generate_password_hash
from datetime import datetime
from app import app  # Asegúrate de importar correctamente tu aplicación Flask

def populate_data():
    with app.app_context():  # Corrección para trabajar dentro del contexto de la aplicación
        # Clear existing data (use with caution in a real application)
        db.session.query(User).delete()
        db.session.query(Attendance).delete()
        db.session.query(Config).delete()
        db.session.query(MeetingCenter).delete()
        db.session.query(Classes).delete()

        # Populate Meeting Centers
        meeting_centers = [
            MeetingCenter(id=1, unit_number=430617, name='Tooele 9th Ward (Spanish)', city='Tooele'),
            MeetingCenter(id=2, unit_number=430620, name='Lucero Ward', city='Salt Lake City')
        ]
        db.session.bulk_save_objects(meeting_centers)

        # Populate Users
        users = [
            User(id=1, username='HenryDiaz', email='henrydiazlds123@hotmail.com', name='Henry', lastname='Diaz',
                 password_hash=generate_password_hash('Diaz_3421'), role='Owner', meeting_center_id=1),
            User(id=2, username='JeffreyBaron', email='jeffrey.baron@gmail.com', name='Jeffrey', lastname='Baron',
                 password_hash=generate_password_hash('Secretario'), role='User', meeting_center_id=2)
        ]
        db.session.bulk_save_objects(users)

        # Populate Config
        configs = [
            Config(id=1, key='code_verification', value='true')
        ]
        db.session.bulk_save_objects(configs)

        # Populate Classes
        classes = [
            Classes(id=1, class_name='Quórum de Elderes', short_name='Q_Elderes', class_code='QE', schedule='2,4'),
            Classes(id=2, class_name='Sacerdocio Aarónico', short_name='S_Aarónico', class_code='SA', schedule='2,4'),
            Classes(id=3, class_name='Sociedad de Socorro', short_name='S_Socorro', class_code='SS', schedule='2,4'),
            Classes(id=4, class_name='Mujeres Jóvenes', short_name='M_Jóvenes', class_code='MJ', schedule='2,4'),
            Classes(id=5, class_name='Esc. Dom. Adultos', short_name='E_D_Adultos', class_code='EDA', schedule='1,3'),
            Classes(id=6, class_name='Esc. Dom. Jóvenes', short_name='E_D_Jóvenes', class_code='EDJ', schedule='1,3'),
            Classes(id=7, class_name='Quinto Domingo', short_name='5to_Domingo', class_code='QD', schedule='5')
        ]
        db.session.bulk_save_objects(classes)

        # Populate Attendance
        attendances = [
            Attendance(id=1, student_name='Camejo, Juan', class_id=2, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12), meeting_center_id=1),
            Attendance(id=1, student_name='Giraldo, Anuar', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 8, 33, 32), meeting_center_id=1),
            Attendance(id=2, student_name='Abadia-Vela, Neftali', class_id=2, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 8, 43, 34), meeting_center_id=1),
            Attendance(id=3, student_name='Meneses, Sandro', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 8, 45, 11), meeting_center_id=1),
            Attendance(id=4, student_name='Abadia, Jesus', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 8, 46, 19), meeting_center_id=1),
            Attendance(id=5, student_name='Espinoza, Jareth', class_id=2, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 11, 51), meeting_center_id=1),
            Attendance(id=6, student_name='Ozuna, Gianluca', class_id=2, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 12, 24), meeting_center_id=1),
            Attendance(id=7, student_name='Garcia, Andrew', class_id=2, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 12, 46), meeting_center_id=1),
            Attendance(id=8, student_name='Santamaria, Juan', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 20, 41), meeting_center_id=1),
            Attendance(id=9, student_name='Ramirez, Libertad', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 22, 25), meeting_center_id=1),
            Attendance(id=10, student_name='Vela, Andrea', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 23, 23), meeting_center_id=1),
            Attendance(id=11, student_name='Castro, Monica', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 25, 50), meeting_center_id=1),
            Attendance(id=12, student_name='Corado, Emilia', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 28, 00), meeting_center_id=1),
            Attendance(id=13, student_name='Baron, Jeffrey', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 28, 50), meeting_center_id=1),
            Attendance(id=14, student_name='Gonzalez, Ana', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 30, 25), meeting_center_id=1),
            Attendance(id=15, student_name='Cannon, Mayra', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 31, 15), meeting_center_id=1),
            Attendance(id=16, student_name='Higuera, Ammy', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 32, 39), meeting_center_id=1),
            Attendance(id=17, student_name='Quispe, Natalia', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 32, 54), meeting_center_id=1),
            Attendance(id=18, student_name='Santos, Ramon', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 33, 13), meeting_center_id=1),
            Attendance(id=19, student_name='Espinosa, Elena', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 33, 38), meeting_center_id=1),
            Attendance(id=20, student_name='Salazar, Juana', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 36, 00), meeting_center_id=1),
            Attendance(id=21, student_name='Polite, Brian', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 36, 9), meeting_center_id=1),
            Attendance(id=22, student_name='Gomez, Cleotilde', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 36, 12), meeting_center_id=1),
            Attendance(id=23, student_name='Thygerson, Samuel', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 36, 13), meeting_center_id=1),
            Attendance(id=24, student_name='Brenchley, Estela', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 36, 22), meeting_center_id=1),
            Attendance(id=25, student_name='Tolentino, Emery', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 36, 48), meeting_center_id=1),
            Attendance(id=26, student_name='Juarez, Diana', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 37, 35), meeting_center_id=1),
            Attendance(id=27, student_name='Corado, Jorge', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 37, 41), meeting_center_id=1),
            Attendance(id=28, student_name='Welch, Jasmine', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 37, 51), meeting_center_id=1),
            Attendance(id=29, student_name='Villamar, Dimitri', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 38, 10), meeting_center_id=1),
            Attendance(id=30, student_name='Gates, Logan', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 38, 16), meeting_center_id=1),
            Attendance(id=31, student_name='Cannon, Patrick', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 38, 47), meeting_center_id=1),
            Attendance(id=32, student_name='Garcia, Sonia', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 39, 17), meeting_center_id=1),
            Attendance(id=33, student_name='Carrasquero, Nelson', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 39, 43), meeting_center_id=1),
            Attendance(id=34, student_name='Navez, María', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 40, 8), meeting_center_id=1),
            Attendance(id=35, student_name='Larsen, Dwayne', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 40, 26), meeting_center_id=1),
            Attendance(id=36, student_name='Lopez, Edgard', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 40, 48), meeting_center_id=1),
            Attendance(id=37, student_name='Giraldo, Diana', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 40, 52), meeting_center_id=1),
            Attendance(id=38, student_name='Mia, Navez', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 40, 52), meeting_center_id=1),
            Attendance(id=39, student_name='Larsen, Maria', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 44, 8), meeting_center_id=1),
            Attendance(id=40, student_name='Gonzalez, Lynn', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 44, 41), meeting_center_id=1),
            Attendance(id=41, student_name='Marín, Carolina', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 44, 50), meeting_center_id=1),
            Attendance(id=42, student_name='Maria, Paisig', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 45, 20), meeting_center_id=1),
            Attendance(id=43, student_name='Garcia, Betzabe', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 45, 54), meeting_center_id=1),
            Attendance(id=44, student_name='Sanchez, Reyna', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 46, 16), meeting_center_id=1),
            Attendance(id=45, student_name='Suárez, Lidia', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 46, 44), meeting_center_id=1),
            Attendance(id=46, student_name='Wexels, Cameron', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 47, 6), meeting_center_id=1),
            Attendance(id=47, student_name='Diaz, Camille', class_id=4, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 47, 40), meeting_center_id=1),
            Attendance(id=48, student_name='Vela, Camila', class_id=4, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 47, 44), meeting_center_id=1),
            Attendance(id=49, student_name='Menchaca, Rogelio', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 47, 49), meeting_center_id=1),
            Attendance(id=50, student_name='Tolentino, Marely', class_id=4, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 47, 55), meeting_center_id=1),
            Attendance(id=51, student_name='Sanchez, Leonel', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 47, 56), meeting_center_id=1),
            Attendance(id=52, student_name='Santamaria, Kiara', class_id=4, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 48, 36), meeting_center_id=1),
            Attendance(id=53, student_name='Tolentino, Karla', class_id=4, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 48, 59), meeting_center_id=1),
            Attendance(id=54, student_name='Sandoval, Viviana', class_id=4, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 49, 9), meeting_center_id=1),
            Attendance(id=55, student_name='Gates, Kathia', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 53, 57), meeting_center_id=1),
            Attendance(id=56, student_name='Navez, Brittany', class_id=4, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 54, 17), meeting_center_id=1),
            Attendance(id=57, student_name='Ozuna, Camila', class_id=4, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 54, 25), meeting_center_id=1),
            Attendance(id=58, student_name='Alfaro, Irina', class_id=4, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 54, 53), meeting_center_id=1),
            Attendance(id=59, student_name='Martinez, Claire', class_id=4, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 55, 7), meeting_center_id=1),
            Attendance(id=60, student_name='Vanderpool, Detzani', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 56, 32), meeting_center_id=1),
            Attendance(id=61, student_name='Mickelson, Natyeli', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 56, 38), meeting_center_id=1),
            Attendance(id=62, student_name='Martinez, Melissa', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 57, 4), meeting_center_id=1),
            Attendance(id=63, student_name='Tolentino, Maritza', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 58, 16), meeting_center_id=1),
            Attendance(id=64, student_name='Ozuna, Nancy', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 58, 29), meeting_center_id=1),
            Attendance(id=65, student_name='Gonzalez, Rosa', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 10, 59, 10), meeting_center_id=1),
            Attendance(id=66, student_name='Aguero, Agustina', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 11, 1, 00), meeting_center_id=1),
            Attendance(id=67, student_name='Lopez, Anne', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 11, 1, 36), meeting_center_id=1),
            Attendance(id=68, student_name='Giraldo, Tawny', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 11, 3, 20), meeting_center_id=1),
            Attendance(id=69, student_name='Diaz, Natalia', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 11, 3, 58), meeting_center_id=1),
            Attendance(id=70, student_name='Marin, Virginia', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 11, 4, 5), meeting_center_id=1),
            Attendance(id=71, student_name='Navez, Israel', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 11, 6, 45), meeting_center_id=1),
            Attendance(id=72, student_name='Cardona, Juan', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 11, 6, 57), meeting_center_id=1),
            Attendance(id=73, student_name='Tolentino, Jose', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 11, 7, 52), meeting_center_id=1),
            Attendance(id=74, student_name='Sandoval, Cesar', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 11, 7, 56), meeting_center_id=1),
            Attendance(id=75, student_name='Aguilar, Barbara', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 11, 8, 55), meeting_center_id=1),
            Attendance(id=76, student_name='Wexels, Jack', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 11, 9, 3), meeting_center_id=1),
            Attendance(id=77, student_name='Cooper, Darren', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 11, 13, 37), meeting_center_id=1),
            Attendance(id=78, student_name='Salcedo, Maria', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 11, 13, 43), meeting_center_id=1),
            Attendance(id=79, student_name='Villamar, Sarah', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 11, 30, 32), meeting_center_id=1),
            Attendance(id=80, student_name='Sandoval, Noemí', class_id=3, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 12, 26, 50), meeting_center_id=1),
            Attendance(id=81, student_name='Diaz, Henry', class_id=1, sunday_date=datetime(2025, 1, 12).date(), sunday_code=845, submit_date=datetime(2025, 1, 12, 14, 35, 18), meeting_center_id=1)
        ]
        db.session.bulk_save_objects(attendances)

        # Commit all changes
        try:
            db.session.commit()
            print("Data populated successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error populating data: {e}")

if __name__ == '__main__':
    populate_data()
