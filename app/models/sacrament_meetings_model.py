# app/models/sacrament_meeting.py
from app.models import db


class SacramentMeeting(db.Model):
    id                = db.Column(db.Integer, primary_key=True)
    sunday_date       = db.Column(db.Date, nullable=False, unique=True)
    director_id       = db.Column(db.Integer, db.ForeignKey('bishopric.id'), nullable=False)
    meeting_center_id = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)
    
    director = db.relationship('Bishopric', backref='meetings')
    agenda   = db.relationship('SacramentAgenda', backref='meeting', uselist=False, cascade="all, delete")
