# app/forms/hymn.py
from flask_wtf          import FlaskForm
from flask_babel        import _
from wtforms.validators import DataRequired, Length
from wtforms.validators import DataRequired, Length
from wtforms            import StringField, IntegerField


#==================================================================================================
class HymnForm(FlaskForm):
    number = IntegerField('Número del himno', validators=[DataRequired()])
    title = StringField('Título del himno', validators=[DataRequired(), Length(max=200)])