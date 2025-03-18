# app/models/base.py
from datetime     import datetime
from flask_babel  import _
from app.models   import db

    
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
        db.UniqueConstraint('key', 'meeting_center_id', name='unique_key_meeting_center'),
    )




