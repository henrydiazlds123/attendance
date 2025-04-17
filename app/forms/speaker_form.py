# app/forms/speaker.py
from flask_wtf          import FlaskForm
from flask_babel        import lazy_gettext as _l, _
from flask_wtf import FlaskForm
from wtforms import DateField, StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class SpeakerForm(FlaskForm):
    sunday_date       = DateField(_l('Sunday Date'), format='%Y-%m-%d', validators=[DataRequired(message="Please select a valid date.")])
    youth_speaker_id  = SelectField('Youth Speaker', coerce=int, validators=[Optional()])
    youth_topic       = StringField('Youth Topic', validators=[Optional()])
    speaker_1_id      = SelectField('Speaker 1', coerce=int, validators=[Optional()])
    topic_1           = StringField('Topic 1', validators=[Optional()])
    speaker_2_id      = SelectField('Speaker 2', coerce=int, validators=[Optional()])
    topic_2           = StringField('Topic 2', validators=[Optional()])
    speaker_3_id      = SelectField('Speaker 3', coerce=int, validators=[Optional()])
    topic_3           = StringField('Topic 3', validators=[Optional()])
    meeting_center_id = SelectField(_('Meeting Center'),coerce=int,validators=[DataRequired(message="Please select a meeting center.")] )
    # Submit Button
    #submit = SubmitField('Save')
