from flask import session
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, PasswordField, DateField, SelectField, TimeField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, ValidationError
from datetime import datetime, timedelta
from wtforms.validators import Regexp



#==================================================================================================
class UserForm(FlaskForm):
    username            = StringField('Username', validators=[DataRequired(), Length(max=80)])
    email               = StringField('Email', validators=[Email(), Length(max=120)])
    password            = PasswordField('Password', validators=[DataRequired()])
    password_confirm    = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    name                = StringField('Name', validators=[DataRequired(), Length(max=20)])
    lastname            = StringField('Lastname', validators=[DataRequired(), Length(max=20)])
    role                = SelectField('Role', choices=[], default='User')
    organization_id     = SelectField('Organization', coerce=int, validators=[DataRequired()])
    meeting_center_id   = SelectField('Unit', coerce=int, validators=[DataRequired()])
    is_active           = BooleanField('Is Active?', default=True)

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        
        # Si hay un rol en la sesión, personalizamos las opciones del rol
        if 'role' in session:
            if session['role'] == 'Owner':
                # Si el usuario es Owner, puede ver todos los roles
                self.role.choices = [('Owner', 'Owner'), ('Admin', 'Admin'), ('User', 'User')]
            else:
                # Si el usuario no es Owner, no se muestra 'Owner' en la lista
                self.role.choices = [('Admin', 'Admin'), ('User', 'User')]

            # Si no es Owner, no puede cambiar el Meeting Center
            if session['role'] != 'Owner':
                self.meeting_center_id.data = session.get('meeting_center_id')
                self.meeting_center_id.render_kw = {'disabled': 'disabled'}

    def validate(self, extra_validators=None):
        # Verifica que el usuario no pueda cambiar el Meeting Center si no es Owner
        if 'role' in session and session['role'] != 'Owner' and self.meeting_center_id.data != session.get('meeting_center_id'):
            self.meeting_center_id.errors.append('No puedes cambiar el Meeting Center.')
            return False
        return super(UserForm, self).validate(extra_validators=extra_validators)

#==================================================================================================
class EditUserForm(FlaskForm):
    username            = StringField('Username', validators=[DataRequired(), Length(max=80)])
    email               = StringField('Email', validators=[Email(), Length(max=120)])
    name                = StringField('Name', validators=[DataRequired(), Length(max=20)])
    lastname            = StringField('Lastname', validators=[DataRequired(), Length(max=20)])
    role                = SelectField('Role', choices=[], default='User')
    organization_id     = SelectField('Organization', coerce=int, validators=[DataRequired()])
    is_active           = BooleanField('Is Active?', default=True)
    meeting_center_id   = SelectField('Unit', coerce=int, validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        if 'role' in session:
            if session['role'] == 'Admin':
                self.role.choices = [('User', 'User'), ('Admin', 'Admin')]
            else:
                self.role.choices = [('Owner', 'Owner'), ('Admin', 'Admin'), ('User', 'User')]

            if session['role'] != 'Owner':
                self.meeting_center_id.data = session.get('meeting_center_id')
                self.meeting_center_id.render_kw = {'disabled': 'disabled'}

    def validate(self, extra_validators=None):
        if 'role' in session and session['role'] != 'Owner' and self.meeting_center_id.data != session.get('meeting_center_id'):
            self.meeting_center_id.errors.append('No puedes cambiar el Meeting Center.')
            return False
        return super(EditUserForm, self).validate(extra_validators=extra_validators)

#==================================================================================================
class ResetPasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password     = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])

#==================================================================================================
class MeetingCenterForm(FlaskForm):
    name        = StringField('Unit Name', validators=[DataRequired(), Length(max=100)])
    unit_number = StringField('Unit #', validators=[DataRequired(), Length(max=10)])
    short_name  = StringField('Short name', validators=[DataRequired(), Length(max=20)])
    city        = StringField('City', validators=[Optional(), Length(max=100)])
    start_time  = TimeField('Start Time', validators=[DataRequired(message="La hora de inicio es obligatoria.")])
    end_time    = TimeField('End Time', validators=[DataRequired(message="La hora de fin es obligatoria.")])


#==================================================================================================
class AttendanceForm(FlaskForm):
    student_name        = SelectField('Student Name', choices=[('', 'Select a name')], coerce=str, validate_choice=False)
    new_student_name    = StringField('New Student Name', validators=[Length(max=100)])
    class_id            = SelectField('Class', choices=[], coerce=int)
    sunday_date         = DateField('Sunday Date', format='%Y-%m-%d', validators=[DataRequired()])
    meeting_center_id   = SelectField('Unit', coerce=int, validators=[DataRequired()])

    def validate_sunday_date(self, field):
        """Validates that sunday_date is not a future date."""
        today = datetime.now().date()
        if field.data > today:
            raise ValidationError("Sunday Date cannot be a future date.")
    
    def set_default_sunday_date(self):
        """Sets default sunday_date to last Sunday if today is not Sunday, otherwise uses today."""
        today = datetime.now().date()
        # Calculate the most recent Sunday
        days_since_sunday       = today.weekday()  # 0 = Monday, 6 = Sunday
        last_sunday             = today - timedelta(days=days_since_sunday + 1) if today.weekday() != 6 else today
        self.sunday_date.data   = last_sunday

#==================================================================================================
class AttendanceEditForm(FlaskForm):
    student_name        = StringField('Student Name', validators=[Length(max=100)])
    class_id            = SelectField('Class', choices=[], coerce=int)
    sunday_date         = DateField('Sunday Date', format='%Y-%m-%d', validators=[DataRequired()])
    # meeting_center_id   = SelectField('Unit', coerce=int, validators=[DataRequired()])
    
#==================================================================================================    

class ClassForm(FlaskForm):
    class_name        = StringField('Class Name', validators=[DataRequired(), Length(max=50)])
    short_name        = StringField('Short Name', validators=[DataRequired(), Length(max=20)])
    class_code        = StringField('Class Code', validators=[DataRequired(), Length(max=10)])
    class_type        = SelectField('Class Type', choices=[('Main', 'Main'), ('Extra', 'Extra')], default='Extra')
    schedule          = StringField('Schedule', validators=[Length(max=10)])
    is_active         = BooleanField('Is Active?', default=True)
    class_color       = StringField('Hex Color', validators=[Length(max=7), Regexp(r'^#(?:[0-9a-fA-F]{3}){1,2}$', message="Invalid color format")])
    meeting_center_id = SelectField('Meeting Center', coerce=int, validators=[DataRequired()])
    
    def __init__(self, *args, **kwargs):
        super(ClassForm, self).__init__(*args, **kwargs)
        if 'role' in session:
            if session['role'] != 'Owner':
                self.meeting_center_id.data = session.get('meeting_center_id')
                self.meeting_center_id.render_kw = {'disabled': 'disabled'}

#==================================================================================================
class OrganizationForm(FlaskForm):
    name = StringField('Organization Name', validators=[DataRequired(), Length(max=50)])
    