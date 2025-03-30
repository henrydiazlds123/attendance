# app/models/selected_hymns.py
from app.models import db

class SelectedHymns(db.Model):
    __tablename__ = 'selected_hymns'

    id                   = db.Column(db.Integer, primary_key=True)
    sunday_date          = db.Column(db.Date, db.ForeignKey('agenda.sunday_date', ondelete="CASCADE"), nullable=False)
    music_director       = db.Column(db.String(50), nullable=True)
    pianist              = db.Column(db.String(50), nullable=True)
    opening_hymn_id      = db.Column(db.Integer, db.ForeignKey('hymns.id'), nullable=True)
    sacrament_hymn_id    = db.Column(db.Integer, db.ForeignKey('hymns.id'), nullable=True)
    intermediate_hymn_id = db.Column(db.Integer, db.ForeignKey('hymns.id'), nullable=True)
    closing_hymn_id      = db.Column(db.Integer, db.ForeignKey('hymns.id'), nullable=True)
    meeting_center_id    = db.Column(db.Integer, nullable=False)  # Nueva columna para el centro de reunión

    # Relación con Agenda usando sunday_date
    agenda = db.relationship('Agenda', back_populates='hymns', foreign_keys=[sunday_date])

    __table_args__ = (
        # Asegurarse de que no se cante el mismo himno más de una vez en el mismo domingo para el mismo meeting_center_id
        db.UniqueConstraint('sunday_date', 'meeting_center_id', 'opening_hymn_id', name='uq_opening_hymn'),
        db.UniqueConstraint('sunday_date', 'meeting_center_id', 'sacrament_hymn_id', name='uq_sacrament_hymn'),
        db.UniqueConstraint('sunday_date', 'meeting_center_id', 'intermediate_hymn_id', name='uq_intermediate_hymn'),
        db.UniqueConstraint('sunday_date', 'meeting_center_id', 'closing_hymn_id', name='uq_closing_hymn'),
    )
