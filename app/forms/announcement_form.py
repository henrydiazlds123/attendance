# app/forms/announcement.py

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired
from app.models import Agenda

class AnnouncementForm(FlaskForm):
    announcement_text = StringField('Detalles del anuncio', validators=[DataRequired()])
    agenda_id = SelectField('Agenda', coerce=int, validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(AnnouncementForm, self).__init__(*args, **kwargs)
        # Cargar las agendas disponibles
        self.agenda_id.choices = [(agenda.id, f"Agenda {agenda.id}") for agenda in Agenda.query.all()]