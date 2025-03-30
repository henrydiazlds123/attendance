# app/models/bishopric.py
from app.models import db

class Bishopric(db.Model):
    __tablename__ = 'bishopric'
    
    id            = db.Column(db.Integer, primary_key=True)
    member_id     = db.Column(db.Integer, db.ForeignKey('member.id'))
    role          = db.Column(db.String(50), nullable=False)
    meeting_center_id = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)

    member         = db.relationship('Member', backref='bishopric')
    meeting_center = db.relationship('MeetingCenter', backref='bishopric')

    __table_args__ = (
        db.UniqueConstraint('meeting_center_id', 'role', name='uq_bishopric_role_unique'),
    )
