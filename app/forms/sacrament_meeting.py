# app/forms/sacrament_meeting.py
from flask_wtf          import FlaskForm
from flask_babel        import _
from app.models         import Bishopric
from wtforms.validators import DataRequired
from wtforms.validators import DataRequired
from wtforms            import DateField, SelectField


#==================================================================================================
class SacramentMeetingForm(FlaskForm):
    sunday_date = DateField('Fecha de la reunión', format='%Y-%m-%d', validators=[DataRequired()])
    director_id = SelectField('Director', coerce=int, validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(SacramentMeetingForm, self).__init__(*args, **kwargs)
        # Cargar los valores de los obispos para el campo director_id
        self.director_id.choices = [(bishop.id, bishop.name) for bishop in Bishopric.query.all()]

