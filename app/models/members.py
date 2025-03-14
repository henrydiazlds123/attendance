# app/models/members.py
from datetime   import date
from app.models import db


class Member(db.Model):
    id                = db.Column(db.Integer, primary_key=True)
    full_name         = db.Column(db.String(255), nullable=False)
    preferred_name    = db.Column(db.String(100))
    short_name        = db.Column(db.String(50))
    birth_date        = db.Column(db.Date)
    gender            = db.Column(db.String(1), nullable=False)  # 'M' o 'F'
    marital_status    = db.Column(db.String(20))
    priesthood        = db.Column(db.String(50))
    priesthood_office = db.Column(db.String(50))
    address           = db.Column(db.String(255))
    city              = db.Column(db.String(100))
    state             = db.Column(db.String(50))
    zip_code          = db.Column(db.String(15))
    sector            = db.Column(db.String(50))
    lat               = db.Column(db.Float)
    lon               = db.Column(db.Float)
    fix_address       = db.Column(db.String(100))
    excluded          = db.Column(db.Boolean, default=False)
    new               = db.Column(db.Boolean, default=False)
    calling           = db.Column(db.String(100))
    arrival_date      = db.Column(db.Date)
    moved_out         = db.Column(db.Boolean, default=False)
    active            = db.Column(db.Boolean, default=True)
    meeting_center_id = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)
    family_head       = db.Column(db.String(100))

    
    def age(self):
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None
    