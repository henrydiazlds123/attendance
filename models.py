from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin
from config import MOUNTAIN_TZ
from sqlalchemy import Time
from sqlalchemy.orm import validates#+
from sqlalchemy.exc import IntegrityError#

db = SQLAlchemy()


#=======================================================================
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id                = db.Column(db.Integer, primary_key=True)
    username          = db.Column(db.String(80), nullable=False, unique=True)
    email             = db.Column(db.String(120), unique=True)
    name              = db.Column(db.String(20), nullable=False)
    lastname          = db.Column(db.String(20), nullable=False)
    password_hash     = db.Column(db.String(128), nullable=False)
    role              = db.Column(db.String(10), nullable=False, default='User')  # Puede ser 'Owner', 'Admin', 'User'
    is_active         = db.Column(db.Boolean, default=True)
    meeting_center_id = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)  # Clave foránea
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    
#=======================================================================
class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id                  = db.Column(db.Integer, primary_key=True)
    student_name        = db.Column(db.String(50), nullable=False)
    class_id            = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    class_type          = db.Column(db.String(10), nullable=False, default='Main')  # Nuevo campo para tipo de clase
    sunday_date         = db.Column(db.Date, nullable=False)
    sunday_code         = db.Column(db.String(10), nullable=True)
    submit_date         = db.Column(db.DateTime, default=lambda: datetime.now(MOUNTAIN_TZ), nullable=False)
    meeting_center_id   = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)   

    __table_args__ = (db.UniqueConstraint('student_name', 'sunday_date', 'meeting_center_id', name='unique_attendance'),)
    
    @property
    def month(self):
        return self.sunday_date.month

    @property
    def year(self):
        return self.sunday_date.year

    def __repr__(self):
        return f"<Attendance {self.student_name} - {self.class_id} - {self.sunday_date}>"


#=======================================================================
class Config(db.Model):
    __tablename__ = 'config'

    id    = db.Column(db.Integer, primary_key=True)
    key   = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(50), nullable=False)


#=======================================================================
class MeetingCenter(db.Model):
    __tablename__ = 'meeting_center'

    id          = db.Column(db.Integer, primary_key=True)
    unit_number = db.Column(db.Integer, unique=True, nullable=False)
    name        = db.Column(db.String(50), nullable=False)
    city        = db.Column(db.String(50), nullable=True)
    attendances = db.relationship('Attendance', backref=db.backref('meeting_center', lazy=True), cascade="all, delete-orphan")
    users       = db.relationship('User', backref=db.backref('meeting_center', lazy=True), cascade="all, delete-orphan")

    @validates('attendances')
    def validate_no_attendance(self, key, value):
        if self.attendances:
            raise IntegrityError("Cannot delete a meeting center with registered attendance", params={}, statement=None)
        return value

    def delete(self):
        if self.attendances:
            raise ValueError("Cannot delete a meeting center with registered attendance.")
        db.session.delete(self)

#=======================================================================
class Classes(db.Model):
    __tablename__ = 'classes'
    
    id         = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(50), nullable=False, unique=True)
    short_name = db.Column(db.String(20), nullable=False, unique=True)
    class_code = db.Column(db.String(10), nullable=False, unique=True)
    class_type = db.Column(db.String(10), nullable=False, default='Main')
    schedule   = db.Column(db.String(10), nullable=True)
    attendances = db.relationship('Attendance', backref=db.backref('classes', lazy=True), cascade="all, delete-orphan")
    is_active  = db.Column(db.Boolean, nullable=False, default=True)  # Nuevo campo
    color_hex  = db.Column(db.String(7), nullable=True, default="#000000")  # Formato de color hexadecimal
    
    @validates('attendances')
    def validate_no_attendance(self, key, value):
        if self.attendances:
            raise IntegrityError("Cannot delete a class with registered attendance", params={}, statement=None)
        return value

    def delete(self):
        if self.attendances:
            raise ValueError("Cannot delete a class with registered attendance.")
        db.session.delete(self)