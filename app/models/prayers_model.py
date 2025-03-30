# app/models/prayers.py
from app.models import db

class Prayer(db.Model):
    id                    = db.Column(db.Integer, primary_key=True)
    member_id  = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    agenda_id  = db.Column(db.Integer, db.ForeignKey('agenda.id'), nullable=False)  
    type       = db.Column(db.Enum('Opening', 'Closing'), nullable=False)

    member = db.relationship('Member', backref='prayers')
    agenda = db.relationship('Agenda', back_populates='prayers_for_meeting')


    __table_args__ = (
        db.UniqueConstraint('member_id', 'agenda_id', 'type', name='uq_prayer_unique'),
    )