# app/models/speakers.py
from app.models import db


class Speakers(db.Model):
    id                = db.Column(db.Integer, primary_key=True)
    agenda_id         = db.Column(db.Integer, db.ForeignKey('sacrament_agenda.id'), nullable=False)
    name              = db.Column(db.String(100), nullable=False)
    topic             = db.Column(db.String(200), nullable=False)
    meeting_center_id = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)
