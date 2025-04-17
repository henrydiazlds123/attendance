# app/forms/selected_hymns_form.py
from flask_babel        import _
from flask_wtf          import FlaskForm
from wtforms.validators import DataRequired
from wtforms            import DateField, SelectField

class SelectedHymnsForm(FlaskForm):
    sunday_date          = DateField(_('Date'), validators=[DataRequired()])
    music_director       = SelectField(_('Director'), coerce=int, choices=[])
    pianist              = SelectField(_('Pianist'), coerce=int, choices=[])
    opening_hymn_id      = SelectField(_('Opening Hymn'), coerce=int, choices=[])
    sacrament_hymn_id    = SelectField(_('Sacrament Hymn'), coerce=int, choices=[])
    intermediate_hymn_id = SelectField(_('Intermediate/Special Hymn'), coerce=int, choices=[])
    closing_hymn_id      = SelectField(_('Closing Hymn'), coerce=int, choices=[])
