# app/models/announcements.py
from datetime   import date
from app.models import db


class WardAnnouncements(db.Model):
    id                = db.Column(db.Integer, primary_key=True)
    agenda_id         = db.Column(db.Integer, db.ForeignKey('sacrament_agenda.id'), nullable=False)
    details           = db.Column(db.Text, nullable=False)
    meeting_center_id = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)
