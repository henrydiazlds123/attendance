# app/forms/announcement.py
from flask_wtf          import FlaskForm
from flask_babel        import _
from app.models         import SacramentAgenda
from wtforms.validators import DataRequired
from wtforms.validators import DataRequired
from wtforms            import SelectField, TextAreaField


#==================================================================================================
class WardAnnouncementForm(FlaskForm):
    details = TextAreaField('Detalles del anuncio', validators=[DataRequired()])
    agenda_id = SelectField('Agenda', coerce=int, validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(WardAnnouncementForm, self).__init__(*args, **kwargs)
        # Cargar las agendas disponibles para el campo agenda_id
        self.agenda_id.choices = [(agenda.id, f"Agenda {agenda.id}") for agenda in SacramentAgenda.query.all()]