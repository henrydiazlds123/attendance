import csv
from datetime import datetime, date
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Attendance, db  # Replace with your actual module and database configuration

# Replace with your database connection string
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///attendance.db')
engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

def import_attendance_data(csv_filename, meeting_center_id):
    with open(csv_filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        records = []

        for row in reader:
            # Parse data into appropriate formats
            sunday_date_parts = [int(part) for part in row['sunday_date'].split(', ')]
            sunday_date = date(*sunday_date_parts)

            submit_date_parts = [int(part) for part in row['submit_date'].split(', ')]
            submit_date = datetime(*submit_date_parts)

            attendance_record = Attendance(
                id=int(row['id']),
                student_name=row['student_name'],
                class_id=int(row['class_id']),
                sunday_date=sunday_date,
                sunday_code=row['sunday_code'],
                submit_date=submit_date,
                meeting_center_id=meeting_center_id
            )
            records.append(attendance_record)
        
        # Bulk insert records into the database
        session.bulk_save_objects(records)
        session.commit()

# Example usage
import_attendance_data('attendance_data.csv', meeting_center_id=1)  # Specify the correct file path and meeting center ID
