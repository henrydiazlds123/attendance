# app/models/agenda.py
from app.models import db

class Agenda(db.Model):
    __tablename__ = 'agenda'
    
    id                  = db.Column(db.Integer, primary_key=True)
    sunday_date         = db.Column(db.Date, nullable=False, unique=True)
    director_id         = db.Column(db.Integer, db.ForeignKey('bishopric.id'), nullable=False)
    presider_id         = db.Column(db.Integer, db.ForeignKey('bishopric.id'), nullable=False)
    opening_prayer      = db.Column(db.String(100), nullable=True)
    closing_prayer      = db.Column(db.String(100), nullable=True)
    meeting_center_id   = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)

    prayers_for_meeting = db.relationship('Prayer',            back_populates='agenda', lazy=True)
    prayers             = db.relationship('Prayer',            back_populates='agenda', lazy=True, overlaps="prayers_for_meeting")
    announcements       = db.relationship('WardAnnouncements', backref='ward_announcements_list', cascade="all, delete", overlaps="ward_announcements_list")
    director            = db.relationship('Bishopric',         foreign_keys=[director_id])
    presider            = db.relationship('Bishopric',         foreign_keys=[presider_id])
    hymns               = db.relationship('SelectedHymns',     back_populates='agenda', cascade="all, delete-orphan", foreign_keys='[SelectedHymns.sunday_date]')
    speakers            = db.relationship('Speaker',           back_populates='agenda', primaryjoin="Agenda.sunday_date == Speaker.sunday_date")

    __table_args__ = (
        db.UniqueConstraint('meeting_center_id', 'sunday_date', name='uq_sacrament_meeting_unique'),
    )
