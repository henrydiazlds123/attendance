# app/models/sacramental_agenda.py
from app.models import db


class SacramentAgenda(db.Model):
    id                = db.Column(db.Integer, primary_key=True)
    meeting_id        = db.Column(db.Integer, db.ForeignKey('sacrament_meeting.id'), nullable=False, unique=True)
    opening_hymn_id   = db.Column(db.Integer, db.ForeignKey('hymns.id'))
    sacrament_hymn_id = db.Column(db.Integer, db.ForeignKey('hymns.id'))
    closing_hymn_id   = db.Column(db.Integer, db.ForeignKey('hymns.id'))
    music_director    = db.Column(db.String(100), nullable=True)
    opening_prayer    = db.Column(db.String(100), nullable=True)
    closing_prayer    = db.Column(db.String(100), nullable=True)
    meeting_center_id = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)
    
    opening_hymn   = db.relationship('Hymns', foreign_keys=[opening_hymn_id])
    sacrament_hymn = db.relationship('Hymns', foreign_keys=[sacrament_hymn_id])
    closing_hymn   = db.relationship('Hymns', foreign_keys=[closing_hymn_id])
    speakers       = db.relationship('Speakers', backref='agenda', cascade="all, delete")
    announcements  = db.relationship('WardAnnouncements', backref='agenda', cascade="all, delete")
