from flask import session
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, PasswordField, DateField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, ValidationError
from datetime import datetime, timedelta



#==================================================================================================
class UserForm(FlaskForm):
    username            = StringField('Username', validators=[DataRequired(), Length(max=80)])
    email               = StringField('Email', validators=[Email(), Length(max=120)])
    password            = PasswordField('Password', validators=[DataRequired()])
    password_confirm    = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    name                = StringField('Name', validators=[DataRequired(), Length(max=20)])
    lastname            = StringField('Lastname', validators=[DataRequired(), Length(max=20)])
    role                = SelectField('Role', choices=[], default='User')
    meeting_center_id   = SelectField('Unit', coerce=int, validators=[DataRequired()])
    is_active           = BooleanField('Is Active?', default=True)

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        if 'role' in session:
            if session['role'] == 'Admin':
                # Limita los roles disponibles para los Admin
                self.role.choices = [('User', 'User'), ('Admin', 'Admin')]
            else:
                # Permite todos los roles para el Owner
                self.role.choices = [('Owner', 'Owner'), ('Admin', 'Admin'), ('User', 'User')]

            if session['role'] != 'Owner':
                self.meeting_center_id.data = session.get('meeting_center_id')
                self.meeting_center_id.render_kw = {'disabled': 'disabled'}

    def validate(self, extra_validators=None):
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
    meeting_center_id   = SelectField('Unit', coerce=int, validators=[DataRequired()])
    is_active           = BooleanField('Is Active?', default=True)

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
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])

#==================================================================================================
class MeetingCenterForm(FlaskForm):
    unit_number   = StringField('Unit #', validators=[DataRequired(), Length(max=20)])
    name          = StringField('Name', validators=[DataRequired(), Length(max=100)])
    city          = StringField('City', validators=[Optional(), Length(max=100)])

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