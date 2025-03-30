# app/models/bussines.py
from app.models import db

class WardBusiness(db.Model):
    __tablename__ = 'ward_business'

    id                    = db.Column(db.Integer, primary_key=True)
    agenda_id             = db.Column(db.Integer, db.ForeignKey('agenda.id'), nullable=False)  # FIXED
    type                  = db.Column(db.Enum('release', 'calling', 'welcome', 'confirmation', 'priesthood', 'baby_blessing', name='business_types'), nullable=False)
    member_id             = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)  
    calling_name          = db.Column(db.String(255), nullable=True)
    baby_name             = db.Column(db.String(255), nullable=True)
    blessing_officiant_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)
    meeting_center_id     = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)

    agenda    = db.relationship('Agenda', backref=db.backref('ward_business', lazy=True))  # FIXED
    member    = db.relationship('Member', foreign_keys=[member_id])
    officiant = db.relationship('Member', foreign_keys=[blessing_officiant_id])

    def __repr__(self):
        return f"<WardBusiness(id={self.id}, type={self.type})>"

