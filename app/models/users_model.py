# app/models/user.py
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login       import UserMixin
from flask_babel       import _
from app.models        import db


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