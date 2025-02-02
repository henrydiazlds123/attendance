from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime          import datetime
from flask_login       import UserMixin
from config            import Config
from sqlalchemy.orm    import validates
from sqlalchemy.exc    import IntegrityError
from sqlalchemy        import UniqueConstraint
from flask_babel       import _



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
    organization_id   = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)  # Clave foránea
    
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
    class_code          = db.Column(db.String(5), nullable=True)
    sunday_date         = db.Column(db.Date, nullable=False)
    sunday_code         = db.Column(db.String(10), nullable=True)
    submit_date         = db.Column(db.DateTime, default=lambda: datetime.now(Config.MOUNTAIN_TZ), nullable=False)
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
    
#=======================================================================
class NameCorrections(db.Model):
    __tablename__ = 'name_corrections'
    
    id                = db.Column(db.Integer, primary_key=True)
    wrong_name        = db.Column(db.String(50), nullable=False, unique=False)
    correct_name      = db.Column(db.String(50), nullable=False)
    meeting_center_id = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)
    added_by          = db.Column(db.String(50), nullable=True)  # Opcional: para registrar quién hizo la corrección
    created_at        = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('wrong_name', 'meeting_center_id', name='uq_wrong_name_meeting_center'),
    )
    
    
#=======================================================================
class Setup(db.Model):
    __tablename__ = 'setup'

    id                = db.Column(db.Integer, primary_key=True)
    key               = db.Column(db.String(50), nullable=False)
    value             = db.Column(db.String(50), nullable=False)
    meeting_center_id = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False, index=True)

    meeting_center = db.relationship('MeetingCenter', backref=db.backref('setup', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('key', 'meeting_center_id', name='_key_meeting_center_uc'),
    )


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

#=======================================================================      
class Classes(db.Model):
    __tablename__     = 'classes'

    id                = db.Column(db.Integer, primary_key=True)
    class_name        = db.Column(db.String(50), nullable=False)
    short_name        = db.Column(db.String(20), nullable=False)
    class_code        = db.Column(db.String(10), nullable=False)
    class_type        = db.Column(db.String(10), nullable=False, default='Extra')
    schedule          = db.Column(db.String(10), nullable=True)
    is_active         = db.Column(db.Boolean, nullable=False, default=True)
    class_color       = db.Column(db.String(7), nullable=True, default="#000000")
    meeting_center_id = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)

    attendances       = db.relationship('Attendance', backref=db.backref('classes', lazy=True), cascade="all, delete-orphan")

    # Unique constraint for class_code, class_name, and short_name within the same meeting_center
    __table_args__    = (
        UniqueConstraint('class_code', 'meeting_center_id', name='uq_class_code_meeting_center'),
        UniqueConstraint('class_name', 'meeting_center_id', name='uq_class_name_meeting_center'),
        UniqueConstraint('short_name', 'meeting_center_id', name='uq_short_name_meeting_center'),
    )

    @validates('attendances')
    def validate_no_attendance(self, key, value):
        if self.attendances:
            raise IntegrityError(_('Cannot delete a class with registered attendance.'), params={}, statement=None)
        return value

    def delete(self):
        if self.attendances:
            raise ValueError(_('Cannot delete a class with registered attendance.'))
        db.session.delete(self) 
        
    @property
    def translated_name(self):
        return _(self.class_name)  # Devuelve el nombre traducido       
        
#=======================================================================        

class Organization(db.Model):
    __tablename__ = 'organization'

    id    = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String(50), unique=True, nullable=False)
    users = db.relationship('User', backref=db.backref('organization', lazy=True), cascade="all, delete-orphan")
    
    def delete(self):
        # Check if there are users associated before trying to delete
        if self.users:
            raise ValueError(_('Cannot delete a church unit with registered attendance.'))
        
        # If no users are associated, proceed to delete
        db.session.delete(self)
        
    @property
    def translated_name(self):
        return _(self.name)  # Devuelve el nombre traducido 
