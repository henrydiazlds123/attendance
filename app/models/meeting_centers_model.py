# app/models/meeting_center.py
from sqlalchemy.orm    import validates
from sqlalchemy.exc    import IntegrityError
from flask_babel       import _
from app.models        import db


#=======================================================================
class MeetingCenter(db.Model):
    __tablename__ = 'meeting_center'

    id                 = db.Column(db.Integer, primary_key=True)
    unit_number        = db.Column(db.Integer, unique=True, nullable=False)
    name               = db.Column(db.String(50), nullable=False)
    short_name         = db.Column(db.String(20), nullable=False)
    city               = db.Column(db.String(50), nullable=True)
    start_time         = db.Column(db.Time, nullable=True)
    end_time           = db.Column(db.Time, nullable=True)
    is_restricted      = db.Column(db.Boolean, default=False)
    grace_period_hours = db.Column(db.Integer, nullable=True, default=0)
    attendances        = db.relationship('Attendance', backref=db.backref('meeting_center', lazy=True), cascade="all, delete-orphan")
    users              = db.relationship('User',       backref=db.backref('meeting_center', lazy=True), cascade="all, delete-orphan")
    classes            = db.relationship('Classes',    backref=db.backref('meeting_center', lazy=True), cascade="all, delete-orphan")

    @validates('attendances')
    def validate_no_attendance(self, key, value):
        if self.attendances:
            raise IntegrityError(_('Cannot delete a church unit with registered attendance.'), params={}, statement=None)
        return value

    def delete(self):
        if self.attendances:
            raise ValueError(_('Cannot delete a church unit with registered attendance.'))
        db.session.delete(self)
