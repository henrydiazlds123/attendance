# app/forms/ward_announcement.py

from flask_wtf import FlaskForm
from flask_babel import _
from app.models import Agenda
from wtforms import FieldList, FormField
from app.forms import AnnouncementForm  # Importar el formulario de anuncios

class WardAnnouncementForm(FlaskForm):
    # Define FieldList for dynamic form fields
    announcements = FieldList(FormField(AnnouncementForm), min_entries=1)

    def __init__(self, *args, **kwargs):
        super(WardAnnouncementForm, self).__init__(*args, **kwargs)
        # Cargar las agendas disponibles para el campo agenda_id
        # Nota: Necesitas acceder a `AnnouncementForm` para cargar sus opciones
        for form in self.announcements:
            form.agenda_id.choices = [(agenda.id, f"Agenda {agenda.id}") for agenda in Agenda.query.all()]
