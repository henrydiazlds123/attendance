# app/forms/organization.py
from flask_wtf          import FlaskForm
from flask_babel        import _
from wtforms.validators import DataRequired, Length
from wtforms.validators import DataRequired, Length
from wtforms            import StringField


#==================================================================================================
class OrganizationForm(FlaskForm):
    name = StringField(_('Organization Name'), validators=[DataRequired(), Length(max=50)])

 