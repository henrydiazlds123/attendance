# app/models/hymns.py
from app.models import db


class Hymns(db.Model):
    id     = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False, unique=True)
    title  = db.Column(db.String(200), nullable=False)
    lang   = db.Column(db.String(5), nullable=False)
