# app/models/bussines.py
from app.models import db

    
class WardBusiness(db.Model):
    __tablename__ = 'ward_business'

    id                    = db.Column(db.Integer, primary_key=True)
    agenda_id             = db.Column(db.Integer, db.ForeignKey('sacrament_agenda.id'), nullable=False)  # Reference to SacramentAgenda
    type                  = db.Column(db.Enum('release', 'calling', 'welcome', 'confirmation', 'priesthood', 'baby_blessing', name='business_types'), nullable=False)
    member_id             = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)  # NULL if type is baby_blessing
    calling_name          = db.Column(db.String(255), nullable=True)
    baby_name             = db.Column(db.String(255), nullable=True)  # Only for baby_blessing
    blessing_officiant_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)  # Only for baby_blessing
    meeting_center_id     = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)

    agenda    = db.relationship('SacramentAgenda', backref=db.backref('ward_business', lazy=True))  # Fix relationship
    member    = db.relationship('Member', foreign_keys=[member_id])  # Changed from Member to User
    officiant = db.relationship('Member', foreign_keys=[blessing_officiant_id])  # Changed from Member to User

    def __repr__(self):
        return f"<WardBusiness(id={self.id}, type={self.type})>"
