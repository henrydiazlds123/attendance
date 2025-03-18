# app/forms/member.py
import re
from flask_wtf          import FlaskForm
from flask_babel        import lazy_gettext as _l, _
from wtforms.validators import DataRequired, Optional, Length
from wtforms.validators import DataRequired, Length, Optional
from wtforms            import BooleanField, DecimalField, FloatField, StringField, DateField, SelectField, TextAreaField, ValidationError


# Expresión regular para validar el formato Apellido, Nombre
name_regex = r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+,\s[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$'

# =================================================================
def validate_full_name(form, field):
    if not field.data:
        raise ValidationError(_('This field is requiered.'))
    full_name = field.data.strip()
    
    if not re.match(name_regex, field.data):
        raise ValidationError('El nombre debe tener el formato: Apellidos, Nombres')

# =================================================================    
def validate_short_name(form, field):
    if not re.match(name_regex, field.data):
        raise ValidationError('El nombre debe tener el formato: Apellido, Nombre')
    

# =================================================================
class MemberForm(FlaskForm):
    full_name         = StringField(_l('Full Name'), validators=[DataRequired(), Length(max=100), validate_full_name])
    preferred_name    = StringField(_l('Preferred Name'), validators=[Optional(), Length(max=50)])
    short_name        = StringField(_l('Short Name'), validators=[Optional(), Length(max=50), validate_short_name])
    active            = BooleanField(_l('Active'))
    birth_date        = DateField(_l('Birth Date'), format='%Y-%m-%d', validators=[DataRequired()])
    gender            = SelectField(_l('Gender'), choices=[('', _l('--Select--')),("M", "Male"), ("F", "Female")], validators=[DataRequired()])
    address           = TextAreaField(_l('Address'), validators=[Optional(), Length(max=200)])
    city              = StringField(_l('City'), validators=[Optional(), Length(max=100)])
    state             = StringField(_l('State'), validators=[Optional(), Length(max=50)])
    zip_code          = StringField(_l('Zip code'), validators=[Optional(), Length(max=10)])
    sector            = StringField(_l('Sector'), validators=[Optional(), Length(max=50)])
    priesthood        = SelectField(_l('Priesthood'), choices=[('', _l('--Select--')),("Aaronic", "Aaronic"), ("Melchizedek", "Melchizedek")],validators=[Optional(), Length(max=50)])
    priesthood_office = SelectField(_l('Priesthood Office'), choices=[], validators=[Optional(), Length(max=50)])
    arrival_date      = DateField(_l('Arrival Date'), format='%Y-%m-%d', validators=[DataRequired()])
    family_head       = StringField(_l('Head of Family'), validators=[Optional(), Length(max=100)])
    calling           = StringField(_l('Calling'), validators=[Optional(), Length(max=100)])
    lat               = DecimalField(_l('Latitude'), validators=[Optional()])
    lon               = DecimalField(_l('Longitude'), validators=[Optional()])
    fixed_address     = StringField(_l('Fixed Address'), validators=[Optional(), Length(max=100)])
    
        
# =================================================================
class MemberEditForm(FlaskForm):
    active            = BooleanField(_l('Active'))
    full_name         = StringField(_l('Full Name'), validators=[DataRequired(), Length(max=100), validate_full_name])
    preferred_name    = StringField(_l('Preferred Name'), validators=[Optional(), Length(max=50)])
    short_name        = StringField(_l('Short Name'), validators=[Optional(), Length(max=50), validate_short_name])
    birth_date        = DateField(_l('Birth Date'), format='%Y-%m-%d', validators=[DataRequired()])
    gender            = SelectField(_l('Gender'), choices=[("M", "Male"), ("F", "Female")], validators=[DataRequired()])
    address           = TextAreaField(_l('Address'), validators=[Optional(), Length(max=200)])
    city              = StringField(_l('City'), validators=[Optional(), Length(max=100)])
    state             = StringField(_l('State'), validators=[Optional(), Length(max=50)])
    zip_code          = StringField(_l('Zip code'), validators=[Optional(), Length(max=10)])
    sector            = StringField(_l('Sector'), validators=[Optional(), Length(max=50)])
    priesthood        = SelectField(_l('Priesthood'), choices=[("Aaronic", "Aaronic"), ("Melchizedek", "Melchizedek")],validators=[Optional(), Length(max=50)])
    priesthood_office = SelectField(_l('Priesthood Office'), choices=[], validators=[Optional(), Length(max=50)])
    arrival_date      = DateField(_l('Arrival Date'), format='%Y-%m-%d', validators=[DataRequired()])
    family_head       = StringField(_l('Head of Family'), validators=[Optional(), Length(max=100)])
    calling           = StringField(_l('Calling'), validators=[Optional(), Length(max=100)])
    lat               = FloatField(_l('Latitude'), validators=[Optional()])
    lon               = FloatField(_l('Longitude'), validators=[Optional()])
    fixed_address     = StringField(_l('Fixed Address'), validators=[Optional(), Length(max=100)])
    excluded          = BooleanField(_l('Excluded'))
    moved_out         = BooleanField(_l('Moved Out'))
