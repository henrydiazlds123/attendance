# app/forms/speaker.py
from flask_wtf          import FlaskForm
from flask_babel        import _
from app.models         import SacramentAgenda
from wtforms.validators import DataRequired, Length
from wtforms.validators import DataRequired, Length
from wtforms            import StringField, SelectField


#==================================================================================================
class SpeakerForm(FlaskForm):
    name = StringField('Nombre del orador', validators=[DataRequired(), Length(max=100)])
    topic = StringField('Tema', validators=[DataRequired(), Length(max=200)])
    agenda_id = SelectField('Agenda', coerce=int, validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(SpeakerForm, self).__init__(*args, **kwargs)
        # Cargar las agendas disponibles para el campo agenda_id
        self.agenda_id.choices = [(agenda.id, f"Agenda {agenda.id}") for agenda in SacramentAgenda.query.all()]