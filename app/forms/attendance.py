# app/forms/attendance.py
from flask_wtf          import FlaskForm
from flask_babel        import lazy_gettext as _l, _
from datetime           import datetime, timedelta
from wtforms.validators import DataRequired, Length
from wtforms.validators import DataRequired, Length, ValidationError
from wtforms            import StringField, DateField, SelectField


#==================================================================================================
class AttendanceForm(FlaskForm):
    student_name        = SelectField(_l('Student Name'), choices=[('', _l('Select a name'))], coerce=str, validate_choice=False)
    new_student_name    = StringField(_l('New Student Name'), validators=[Length(max=100)])
    class_id            = SelectField(_l('Class'), choices=[], coerce=int)
    sunday_date         = DateField(_l('Sunday Date'), format='%Y-%m-%d', validators=[DataRequired()])
    meeting_center_id   = SelectField(_l('Unit'), coerce=int, validators=[DataRequired()])

    def validate_sunday_date(self, field):
        """Validates that sunday_date is not a future date."""
        today = datetime.now().date()
        if field.data > today:
            raise ValidationError(_('Sunday Date cannot be a future date.'))
    
    def set_default_sunday_date(self):
        """Sets default sunday_date to last Sunday if today is not Sunday, otherwise uses today."""
        today = datetime.now().date()
        # Calculate the most recent Sunday
        days_since_sunday       = today.weekday()  # 0 = Monday, 6 = Sunday
        last_sunday             = today - timedelta(days=days_since_sunday + 1) if today.weekday() != 6 else today
        self.sunday_date.data   = last_sunday
        

#==================================================================================================
class AttendanceEditForm(FlaskForm):
    student_name        = StringField(_l('Student Name'), validators=[Length(max=100)])
    class_id            = SelectField(_l('Class'), choices=[], coerce=int)
    sunday_date         = DateField(_l('Sunday Date'), format='%Y-%m-%d', validators=[DataRequired()])
    # meeting_center_id   = SelectField('Unit', coerce=int, validators=[DataRequired()])
    
    