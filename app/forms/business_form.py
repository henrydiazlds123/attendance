# app/forms/business.py
from flask_wtf          import FlaskForm
from flask_babel        import _
from wtforms.validators import DataRequired, Optional
from wtforms.validators import DataRequired, Optional
from wtforms            import StringField, SelectField, IntegerField

    
class WardBusinessForm(FlaskForm):
    agenda_id = IntegerField('Agenda ID', validators=[DataRequired()])
    type      = SelectField('Type', choices=[('release', 'Release'), ('calling', 'Calling'), ('welcome', 'Welcome'),
                                        ('confirmation', 'Confirmation'), ('priesthood', 'Priesthood'),
                                        ('baby_blessing', 'Baby Blessing')], validators=[DataRequired()])
    member_id             = IntegerField('Member ID', validators=[Optional()])
    calling_name          = StringField('Calling Name', validators=[Optional()])
    baby_name             = StringField('Baby Name', validators=[Optional()])
    blessing_officiant_id = IntegerField('Blessing Officiant ID', validators=[Optional()])