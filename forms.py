from flask              import session
from flask_wtf          import FlaskForm
from flask_babel        import _
from flask_babel        import lazy_gettext as _l
from wtforms            import BooleanField, StringField, PasswordField, DateField, SelectField, TimeField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, ValidationError
from datetime           import datetime, timedelta
from wtforms.validators import Regexp


#==================================================================================================
class UserForm(FlaskForm):
    username            = StringField(_l('Username'), validators=[DataRequired(), Length(max=80)])
    email               = StringField(_l('Email'), validators=[Email(), Length(max=120)])
    password            = PasswordField(_l('Password'), validators=[DataRequired()])
    password_confirm    = PasswordField(_l('Confirm Password'), validators=[DataRequired(), EqualTo('password')])
    name                = StringField(_l('Name'), validators=[DataRequired(), Length(max=20)])
    lastname            = StringField(_l('Lastname'), validators=[DataRequired(), Length(max=20)])
    role                = SelectField(_l('Role'), choices=[], default='User')
    organization_id     = SelectField(_l('Organization'), coerce=int, validators=[DataRequired()])
    meeting_center_id   = SelectField(_l('Unit'), coerce=int, validators=[DataRequired()])
    is_active           = BooleanField(_l('Is Active?'), default=True)

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        
        # Si hay un rol en la sesión, personalizamos las opciones del rol
        if 'role' in session:
            if session['role'] == 'Owner':
                self.role.choices = [('Admin', _('Admin')), ('Super', _('Super user')), ('User', _('User')), ('Operator', _('Operator'))]
            elif session['role'] == 'Admin':
                # Si el usuario no es Owner, no se muestra 'Owner' en la lista
                self.role.choices = [('Admin', _('Admin')), ('Super', _('Super user')), ('Operator', _('Operator'))]
            else:
                # Si el usuario no es Owner, no se muestra 'Owner' en la lista
                self.role.choices = [('Super', _('Super user')), ('User', _('User')), ('Operator', _('Operator'))]

            # Si no es Owner, no puede cambiar el Meeting Center
            if session['role'] != 'Owner':
                self.meeting_center_id.data = session.get('meeting_center_id')
                self.meeting_center_id.render_kw = {'disabled': 'disabled'}

    def validate(self, extra_validators=None):
        # Verifica que el usuario no pueda cambiar el Meeting Center si no es Owner
        if 'role' in session and session['role'] != 'Owner' and self.meeting_center_id.data != session.get('meeting_center_id'):
            self.meeting_center_id.errors.append(_('You cannot change the Church Unit.'))
            return False
        return super(UserForm, self).validate(extra_validators=extra_validators)
    

#==================================================================================================
class EditUserForm(FlaskForm):
    username            = StringField(_l('Username'), validators=[DataRequired(), Length(max=80)])
    email               = StringField(_l('Email'), validators=[Email(), Length(max=120)])
    name                = StringField(_l('Name'), validators=[DataRequired(), Length(max=20)])
    lastname            = StringField(_l('Lastname'), validators=[DataRequired(), Length(max=20)])
    role                = SelectField(_l('Role'), choices=[], default='User')
    organization_id     = SelectField(_l('Organization'), coerce=int, validators=[DataRequired()])
    is_active           = BooleanField(_l('Is Active?'), default=True)
    meeting_center_id   = SelectField(_l('Unit'), coerce=int, validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        # Si hay un rol en la sesión, personalizamos las opciones del rol
        if 'role' in session:
            if session['role'] == 'Owner':
                self.role.choices = [('Admin', _('Admin')), ('Super', _('Super user')), ('User', _('User')), ('Operator', _('Operator'))]
            elif session['role'] == 'Admin':
                # Si el usuario no es Owner, no se muestra 'Owner' en la lista
                self.role.choices = [('Admin', _('Admin')), ('Super', _('Super user')), ('Operator', _('Operator'))]
            else:
                # Si el usuario no es Owner, no se muestra 'Owner' en la lista
                self.role.choices = [('Super', _('Super user')), ('User', _('User')), ('Operator', _('Operator'))]

            # Si no es Owner, no puede cambiar el Meeting Center
            if session['role'] != 'Owner':
                self.meeting_center_id.data = session.get('meeting_center_id')
                self.meeting_center_id.render_kw = {'disabled': 'disabled'}

    def validate(self, extra_validators=None):
        if 'role' in session and session['role'] != 'Owner' and self.meeting_center_id.data != session.get('meeting_center_id'):
            self.meeting_center_id.errors.append(_('You cannot change the Church Unit.'))
            return False
        return super(EditUserForm, self).validate(extra_validators=extra_validators)
    

#==================================================================================================
class ResetPasswordForm(FlaskForm):
    current_password = PasswordField(_l('Current Password'), validators=[DataRequired()])
    new_password     = PasswordField(_l('New Password'), validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(_l('Confirm New Password'), validators=[DataRequired(), EqualTo('new_password', message= _l('Passwords must match'))])
    

#==================================================================================================
class MeetingCenterForm(FlaskForm):
    name               = StringField(_l('Unit Name'), validators=[DataRequired(), Length(max=100)])
    unit_number        = StringField(_l('Unit #'), validators=[DataRequired(), Length(max=10)])
    short_name         = StringField(_l('Short name'), validators=[DataRequired(), Length(max=20)])
    city               = StringField(_l('City'), validators=[Optional(), Length(max=100)])
    start_time         = TimeField(_l('Start Time'), validators=[DataRequired(message=_l('The start time is mandatory'))])
    end_time           = TimeField(_l('End Time'), validators=[DataRequired(message=_l('The end time is mandatory.'))])
    is_restricted      = BooleanField(_l('Is Restricted?'), default=False)
    grace_period_hours = IntegerField(_l('Grace Period (hrs)?'), default=0)


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
    
    
#==================================================================================================    
class ClassForm(FlaskForm):
    class_name  = StringField(_l('Class Name'), validators=[DataRequired(), Length(max=50)])
    short_name  = StringField(_l('Short Name'), validators=[DataRequired(), Length(max=20)])
    class_code  = StringField(_l('Class Code'), validators=[DataRequired(), Length(max=10)])
    class_type  = SelectField(_l('Class Type'), choices=[('Main', _l('Main')), ('Extra', _l('Extra'))], default=_l('Extra'))
    schedule    = StringField(_l('Schedule'), validators=[Length(max=10)])
    is_active   = BooleanField(_l('Is Active?'), default=True)
    class_color = StringField(
        'Hex Color',
        validators=[Length(max=7), Regexp(r'^#(?:[0-9a-fA-F]{3}){1,2}$', message=_l('Invalid color format'))],
        render_kw={'class': 'form-control form-control-color', 'type': 'color', 'value': '#000000'}
    )
    meeting_center_id = SelectField(_l('Church Unit'), coerce=int, validators=[DataRequired()])
    

    def __init__(self, *args, **kwargs):
        # Extraer la instancia de la clase que se está editando, si existe
        obj = kwargs.get('obj')
        super(ClassForm, self).__init__(*args, **kwargs)
        
        # Configurar el color predeterminado solo si el objeto tiene un valor para `class_color`
        if obj and obj.class_color:
            self.class_color.render_kw['value'] = obj.class_color
        else:
            self.class_color.render_kw['value'] = '#000000'  # Valor por defecto

        # Manejo del rol para meeting_center_id y class_type
        if 'role' in session:
            if session['role'] != 'Owner':
                self.meeting_center_id.data = session.get('meeting_center_id')
                self.meeting_center_id.render_kw = {'disabled': 'disabled'}
                self.class_type.render_kw = {'disabled': 'disabled'}
                

#==================================================================================================
class OrganizationForm(FlaskForm):
    name = StringField(_('Organization Name'), validators=[DataRequired(), Length(max=50)])
    