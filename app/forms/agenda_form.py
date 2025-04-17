# app/forms/agenda_form.py
from flask_wtf          import FlaskForm
from wtforms.validators import DataRequired, Optional
from flask_babel        import lazy_gettext as _l, _
from wtforms            import DateField, FieldList, FormField, SelectField, StringField, SubmitField
from app.forms.speaker_form import SpeakerForm
from app.models         import Bishopric, MeetingCenter, Agenda
from app.forms          import AnnouncementForm, WardBusinessForm


#==================================================================================================
class AgendaForm(FlaskForm):
    sunday_date          = DateField('Date', validators=[DataRequired()])
    meeting_center_id    = SelectField(_l('Unit'), coerce=int, validators=[DataRequired()])
    director_id          = SelectField('Dirige', coerce=int, validators=[DataRequired()])
    presider_id          = SelectField('Preside', coerce=int, validators=[DataRequired()])
    opening_prayer       = StringField('Opening Prayer')
    closing_prayer       = StringField('Closing Prayer')
    music_director       = StringField('Music Director')
    pianist              = StringField('Pianist')
    opening_hymn_id      = SelectField('Opening Hymn', coerce=int, choices=[], validators=[DataRequired()])
    sacrament_hymn_id    = SelectField('Sacrament Hymn', coerce=int, choices=[], validators=[DataRequired()])
    intermediate_hymn_id = SelectField('Intermediate/Special Hymn', coerce=int, choices=[])
    closing_hymn_id      = SelectField('Closing Hymn', coerce=int, choices=[], validators=[DataRequired()])
    speakers             = FieldList(FormField(SpeakerForm), min_entries=1) # Speakers dinámicos
    announcements        = FieldList(FormField(AnnouncementForm), min_entries=1)  # Usa FormField Anuncios dinámicos (libres)
    business             = FieldList(FormField(WardBusinessForm), min_entries=1)  # Usa FormField# Asuntos de barrio (libres pero guiados)

    # Agrega agenda_id si es necesario
    agenda_id = SelectField('Agenda ID', coerce=int, choices=[], validators=[Optional()])
    submit    = SubmitField('Save Agenda')

    def __init__(self, *args, **kwargs):
        super(AgendaForm, self).__init__(*args, **kwargs)
        # Puedes mantener las elecciones aquí, si las necesitas
        self.director_id.choices = [(b.id, b.member.preferred_name) for b in Bishopric.query.all()]
        self.presider_id.choices = [(b.id, b.member.preferred_name) for b in Bishopric.query.all()]
        self.meeting_center_id.choices = [(m.id, m.name) for m in MeetingCenter.query.all()]
        self.agenda_id.choices = [(a.id, a.name) for a in Agenda.query.all()]  # Añade opciones dinámicas