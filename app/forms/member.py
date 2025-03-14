# app/forms/member.py
from flask_wtf          import FlaskForm
from flask_babel        import _
from wtforms.validators import DataRequired, Optional, Length
from wtforms.validators import DataRequired, Length, Optional
from wtforms            import BooleanField, DecimalField, StringField, DateField, SelectField, TextAreaField


# =================================================================
class MemberForm(FlaskForm):
    full_name         = StringField("Full Name", validators=[DataRequired(), Length(max=100)])
    preferred_name    = StringField("Preferred Name", validators=[Optional(), Length(max=50)])
    birth_date        = DateField("Birth Date", format='%Y-%m-%d', validators=[Optional()])
    gender            = SelectField("Gender", choices=[("M", "Male"), ("F", "Female")], validators=[DataRequired()])
    priesthood        = StringField("Priesthood", validators=[Optional(), Length(max=50)])
    priesthood_office = StringField("Priesthood Office", validators=[Optional(), Length(max=50)])
    address           = TextAreaField("Address", validators=[Optional(), Length(max=200)])
    city              = StringField("City", validators=[Optional(), Length(max=100)])
    sector            = StringField("Sector", validators=[Optional(), Length(max=100)])
    lat               = DecimalField("Latitude", validators=[Optional()])
    lon               = DecimalField("Longitude", validators=[Optional()])
    fix_address       = BooleanField("Fix Address")
    excluded          = BooleanField("Excluded")
    new               = BooleanField("New Member")
    calling           = StringField("Calling", validators=[Optional(), Length(max=100)])
    arrival_date      = DateField("Arrival Date", format='%Y-%m-%d', validators=[Optional()])
    moved_out         = BooleanField("Moved Out")
    active            = BooleanField("Active")
    status            = StringField("Status", validators=[Optional(), Length(max=50)])
    category          = StringField("Category", validators=[Optional(), Length(max=50)])
    short_name        = StringField("Short Name", validators=[Optional(), Length(max=50)])
    