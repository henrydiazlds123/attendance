# app/models/attendance.py
from datetime          import datetime
from app.config        import Config
from flask_babel       import _
from app.models        import db


#=======================================================================
class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id                  = db.Column(db.Integer, primary_key=True)
    student_name        = db.Column(db.String(50), nullable=False)
    class_id            = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    class_code          = db.Column(db.String(5), nullable=True)
    sunday_date         = db.Column(db.Date, nullable=False)
    sunday_code         = db.Column(db.String(10), nullable=True)
    submit_date         = db.Column(db.DateTime, default=lambda: datetime.now(Config.MOUNTAIN_TZ), nullable=False)
    created_by          = db.Column(db.String(15), nullable=True)
    meeting_center_id   = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)
    fix_name            = db.Column(db.Boolean, default=False) # Nuevo campo para definir si student_name necesita cambiar
    
    __table_args__ = (db.UniqueConstraint('student_name', 'sunday_date', 'meeting_center_id', 'class_id', name='unique_attendance'),)
    
    @property
    def month(self):
        return self.sunday_date.month

    @property
    def year(self):
        return self.sunday_date.year

    def __repr__(self):
        return f"<Attendance {self.student_name} - {self.class_id} - {self.sunday_date}>"