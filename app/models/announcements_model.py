# app/models/ward_announcements.py
from app.models import db

class WardAnnouncements(db.Model):
    __tablename__ = 'ward_announcements'
    id                = db.Column(db.Integer, primary_key=True)
    agenda_id         = db.Column(db.Integer, db.ForeignKey('agenda.id'), nullable=False)
    announcement_text = db.Column(db.String(500), nullable=True)
    
    agenda = db.relationship('Agenda', back_populates='announcements', overlaps="ward_announcements_list")
    
    __table_args__ = (
        db.UniqueConstraint('agenda_id', 'announcement_text', name='uq_ward_announcement_unique'),
    )
