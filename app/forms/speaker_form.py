# app/forms/speaker.py
from flask_wtf          import FlaskForm
from flask_babel        import lazy_gettext as _l, _
from flask_wtf import FlaskForm
from wtforms import DateField, StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class SpeakerForm(FlaskForm):
    sunday_date       = DateField(_('Sunday Date'), format='%Y-%m-%d', validators=[DataRequired(message="Please select a valid date.")])
    youth_speaker_id  = SelectField(_('Youth Speaker'), coerce=int, validators=[DataRequired(message="Please select a youth speaker.")])
    youth_topic       = StringField(_('Youth Topic'),validators=[Length(max=200, message="Youth topic cannot exceed 200 characters.")])
    speaker_1_id      = SelectField(_('1st Speaker'), coerce=int, validators=[DataRequired(message="Please select Speaker 1.")])
    topic_1           = StringField(_('Topic 1'), validators=[Length(max=200, message="Topic 1 cannot exceed 200 characters.")])
    speaker_2_id      = SelectField(_('2nd Speaker'), coerce=int,validators=[DataRequired(message="Please select Speaker 2.")] )
    topic_2           = StringField(_('Topic 2'), validators=[Length(max=200, message="Topic 2 cannot exceed 200 characters.")])
    speaker_3_id      = SelectField(_('3th Speaker'), coerce=int,validators=[DataRequired(message="Please select Speaker 3.")] )
    topic_3           = StringField(_('Topic 3'), validators=[Length(max=200, message="Topic 3 cannot exceed 200 characters.")] )
    meeting_center_id = SelectField(_('Meeting Center'),coerce=int,validators=[DataRequired(message="Please select a meeting center.")] )
    # Submit Button
    submit = SubmitField('Save')
