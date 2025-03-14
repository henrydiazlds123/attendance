# app/models/bishopric.py
from app.models import db


class Bishopric(db.Model):
    id                = db.Column(db.Integer, primary_key=True)
    name              = db.Column(db.String(100), nullable=False)
    role              = db.Column(db.String(50), nullable=False)  # Obispo, Primer Consejero, Segundo Consejero
    meeting_center_id = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)

