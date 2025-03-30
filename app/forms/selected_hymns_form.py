# app/forms/selected_hymns_form.py
from flask_babel        import _
from flask_wtf          import FlaskForm
from wtforms.validators import DataRequired
from wtforms            import DateField, SelectField

class SelectedHymnsForm(FlaskForm):
    sunday_date          = DateField('Date', validators=[DataRequired()])
    opening_hymn_id      = SelectField('Opening Hymn', coerce=int, choices=[])
    sacrament_hymn_id    = SelectField('Sacrament Hymn', coerce=int, choices=[])
    intermediate_hymn_id = SelectField('Intermediate/Special Hymn', coerce=int, choices=[])
    closing_hymn_id      = SelectField('Closing Hymn', coerce=int, choices=[])
