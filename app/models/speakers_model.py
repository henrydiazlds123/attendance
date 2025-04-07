# app/models/speakers.py
from app.models import db

class Speaker(db.Model):
    __tablename__ = 'speaker'

    id                = db.Column(db.Integer, primary_key=True)
    sunday_date       = db.Column(db.Date, db.ForeignKey('agenda.sunday_date'), nullable=False)
    youth_speaker_id  = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)
    youth_topic       = db.Column(db.String(200), nullable=True)
    speaker_1_id      = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)
    topic_1           = db.Column(db.String(200), nullable=True)
    speaker_2_id      = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)
    topic_2           = db.Column(db.String(200), nullable=True)
    speaker_3_id      = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)
    topic_3           = db.Column(db.String(200), nullable=True)
    meeting_center_id = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)

     # Relationships with explicit foreign_keys
    youth_speaker  = db.relationship('Member', foreign_keys=[youth_speaker_id], backref='youth_speakers')
    speaker_1      = db.relationship('Member',foreign_keys=[speaker_1_id],backref='speakers_1')
    speaker_2      = db.relationship('Member',foreign_keys=[speaker_2_id],backref='speakers_2')
    speaker_3      = db.relationship('Member',foreign_keys=[speaker_3_id],backref='speakers_3' )
    agenda         = db.relationship('Agenda', back_populates='speakers', overlaps="speakers")
    # member         = db.relationship('Member', backref='speakers_list')
    meeting_center = db.relationship('MeetingCenter', backref='speakers_list')

    __table_args__ = (
        db.UniqueConstraint('sunday_date', 'meeting_center_id', name='uq_speaker_unique'),
    )