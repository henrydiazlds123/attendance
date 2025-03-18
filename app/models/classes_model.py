# app/models/classes.py
from sqlalchemy.orm    import validates
from sqlalchemy.exc    import IntegrityError
from sqlalchemy        import UniqueConstraint
from flask_babel       import _
from app.models        import db


#=======================================================================
class Classes(db.Model):
    __tablename__ = 'classes'

    id                = db.Column(db.Integer, primary_key=True)
    class_name        = db.Column(db.String(50), nullable=False)
    short_name        = db.Column(db.String(20), nullable=False)
    class_code        = db.Column(db.String(10), nullable=False)
    class_type        = db.Column(db.String(10), nullable=False, default='Extra')
    schedule          = db.Column(db.String(10), nullable=True)
    is_active         = db.Column(db.Boolean, nullable=False, default=True)
    class_color       = db.Column(db.String(7), nullable=True, default="#000000")
    organization_id   = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    meeting_center_id = db.Column(db.Integer, db.ForeignKey('meeting_center.id'), nullable=False)

    # Relaciones
    attendances       = db.relationship('Attendance', backref=db.backref('classes', lazy=True), cascade="all, delete-orphan")
    organization      = db.relationship('Organization', backref=db.backref('classes', lazy=True))

    # Restricciones únicas
    __table_args__ = (
    UniqueConstraint('class_code', 'meeting_center_id', name='uq_class_code_meeting_center'),
    UniqueConstraint('class_name', 'meeting_center_id', name='uq_class_name_meeting_center'),
    UniqueConstraint('short_name', 'meeting_center_id', name='uq_short_name_meeting_center'),
    )

    @validates('attendances')
    def validate_no_attendance(self, key, value):
        if self.attendances:
            raise IntegrityError(_('Cannot delete a class with registered attendance.'), params={}, statement=None)
        return value

    def delete(self):
        if self.attendances:
            raise ValueError(_('Cannot delete a class with registered attendance.'))
        db.session.delete(self)

    @property
    def translated_name(self):
        return _(self.class_name)

    @property
    def translated_short_name(self):
        return _(self.short_name)

    @property
    def translated_code(self):
        return _(self.class_code)