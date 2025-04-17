# app/forms/business_form.py
from flask_wtf          import FlaskForm
from flask_babel        import _
from wtforms.validators import DataRequired, Optional
from wtforms.validators import DataRequired, Optional
from wtforms            import StringField, SelectField, IntegerField, SubmitField


class WardBusinessForm(FlaskForm):
    agenda_id     = IntegerField(_('Agenda ID'), validators=[DataRequired()])
    business_type = SelectField(
        _('Type'),
        choices=[
            ('release', _('Release')),
            ('calling', _('Calling')),
            ('welcome', _('Welcome')),
            ('confirmation', _('Confirmation')),
            ('priesthood', _('Priesthood')),
            ('baby_blessing', _('Baby Blessing'))
        ],
        validators=[DataRequired()]
    )
    member_id             = IntegerField(_('Member ID'), validators=[Optional()])
    calling_name          = StringField(_('Calling Name'), validators=[Optional()])
    baby_name             = StringField(_('Baby Name'), validators=[Optional()])
    blessing_officiant_id = IntegerField(_('Blessing Officiant ID'), validators=[Optional()])
    meeting_center_id     = IntegerField(_('Meeting Center ID'), validators=[DataRequired()])

