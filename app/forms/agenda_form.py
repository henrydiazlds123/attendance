# app/forms/agenda_form.py
from flask_wtf          import FlaskForm
from wtforms.validators import DataRequired
from flask_babel        import lazy_gettext as _l, _
from wtforms            import DateField, FieldList, FormField, SelectField, StringField, SubmitField
from app.forms.hymn_form import HymnForm
from app.forms.speaker_form import SpeakerForm
from app.models         import Bishopric, MeetingCenter
from app.forms          import WardAnnouncementForm, WardBusinessForm


#==================================================================================================
class AgendaForm(FlaskForm):
    sunday_date       = DateField('Date', validators=[DataRequired()])
    director_id       = SelectField('Dirige', coerce=int, validators=[DataRequired()])
    presider_id       = SelectField('Preside', coerce=int, validators=[DataRequired()])
    opening_prayer    = StringField('Opening Prayer')
    closing_prayer    = StringField('Closing Prayer')
    meeting_center_id = SelectField(_l('Unit'), coerce=int, validators=[DataRequired()])

    hymns             = FieldList(FormField(HymnForm), min_entries=1)
    announcements     = FieldList(FormField(WardAnnouncementForm), min_entries=1)
    business          = FieldList(FormField(WardBusinessForm), min_entries=1)
    speakers          = FieldList(FormField(SpeakerForm), min_entries=1)

    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(AgendaForm, self).__init__(*args, **kwargs)
        # Puedes mantener las elecciones aquí, si las necesitas
        self.director_id.choices = [(b.id, b.member.preferred_name) for b in Bishopric.query.all()]
        self.presider_id.choices = [(b.id, b.member.preferred_name) for b in Bishopric.query.all()]
        self.meeting_center_id.choices = [(m.id, m.name) for m in MeetingCenter.query.all()]