# app/models/speakers.py
from app.models import db

class Speaker(db.Model):
    __tablename__ = 'speaker'


    id                = db.Column(db.Integer, primary_key=True)
    sunday_date       = db.Column(db.Date, db.ForeignKey('agenda.sunday_date'), nullable=False)
    member_id         = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    topic             = db.Column(db.String(200), nullable=False)
    meeting_center_id = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)

    #agenda         = db.relationship('Agenda', backref='speakers_list')
    agenda         = db.relationship('Agenda', back_populates='speakers', overlaps="speakers")
    member         = db.relationship('Member', backref='speakers_list')
    meeting_center = db.relationship('MeetingCenter', backref='speakers_list')

    __table_args__ = (
        db.UniqueConstraint('member_id', 'sunday_date', 'meeting_center_id', name='uq_speaker_unique'),
    )