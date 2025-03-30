# app/forms/speaker.py
from flask_wtf          import FlaskForm
from flask_babel        import lazy_gettext as _l, _
from wtforms.validators import DataRequired, Length
from wtforms.validators import DataRequired, Length
from wtforms            import SelectField, StringField

# from app.models import Agenda
import typing
if typing.TYPE_CHECKING:
    from app.models import Agenda


#==================================================================================================
class SpeakerForm(FlaskForm):
    name      = StringField('Speaker Name', validators=[DataRequired(), Length(max=100)])
    topic     = StringField('Topic', validators=[DataRequired(), Length(max=200)])
    agenda_id = SelectField('Agenda', coerce=int, validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(SpeakerForm, self).__init__(*args, **kwargs)
        # Cargar las agendas disponibles para el campo agenda_id
        # self.agenda_id.choices = [(agenda.id, f"Agenda {agenda.id}") for agenda in Agenda.query.all()]
        from app import models
        self.agenda_id.choices = [(agenda.id, f"Agenda {agenda.id}") for agenda in models.Agenda.query.all()]
