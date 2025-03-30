# app/forms/hymn.py
from flask_wtf          import FlaskForm
from flask_babel        import lazy_gettext as _l
from wtforms            import SelectField, StringField, IntegerField
from wtforms.validators import DataRequired, Length
from app.models         import Hymns  # Importamos el modelo



class HymnForm(FlaskForm):
    hymn_number = IntegerField('Número de Himno', validators=[DataRequired()])
    hymn_type = SelectField('Tipo de Himno', choices=[
        ('opening_hymn_id', '1er Himno'),
        ('sacrament_hymn_id', 'Himno Sacramental'),
        ('intermediate_hymn_id', 'Himno Intermedio'),
        ('closing_hymn_id', 'Último Himno')
    ], validators=[DataRequired()])

    
