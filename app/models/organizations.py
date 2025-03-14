# app/models/organization.py
from flask_babel       import _
from app.models        import db


#=======================================================================
class Organization(db.Model):
    __tablename__ = 'organization'

    id    = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String(50), unique=True, nullable=False)
    users = db.relationship('User', backref=db.backref('organization', lazy=True), cascade="all, delete-orphan")
    
    def delete(self):
        # Check if there are users associated before trying to delete
        if self.users:
            raise ValueError(_('Cannot delete a church unit with registered attendance.'))
        
        # If no users are associated, proceed to delete
        db.session.delete(self)
        
    @property
    def translated_name(self):
        return _(self.name)  # Devuelve el nombre traducido 
