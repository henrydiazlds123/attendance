# app/forms/meeting_center.py
from flask_wtf          import FlaskForm
from flask_babel        import lazy_gettext as _l, _
from wtforms.validators import DataRequired, Optional, Length
from wtforms.validators import DataRequired, Length, Optional
from wtforms            import BooleanField, StringField, TimeField, IntegerField


#==================================================================================================
class MeetingCenterForm(FlaskForm):
    name               = StringField(_l('Unit Name'), validators=[DataRequired(), Length(max=100)])
    unit_number        = StringField(_l('Unit #'), validators=[DataRequired(), Length(max=10)])
    short_name         = StringField(_l('Short name'), validators=[DataRequired(), Length(max=20)])
    city               = StringField(_l('City'), validators=[Optional(), Length(max=100)])
    start_time         = TimeField(_l('Start Time'), validators=[DataRequired(message=_l('The start time is mandatory'))])
    end_time           = TimeField(_l('End Time'), validators=[DataRequired(message=_l('The end time is mandatory.'))])
    is_restricted      = BooleanField(_l('Is Restricted?'), default=False)
    grace_period_hours = IntegerField(_l('Grace Period (hrs)?'), default=0)
