# app/forms/user.py
from flask              import session
from flask_wtf          import FlaskForm
from flask_babel        import lazy_gettext as _l, _
from wtforms.validators import DataRequired, Optional, Length
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo
from wtforms            import BooleanField, StringField, PasswordField, SelectField


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

            if (session['role'] != 'Owner' and session['role'] != 'Admin'):
                self.organization_id.data = session.get('organization_id')
                self.organization_id.render_kw = {'disabled': 'disabled'}

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
class ProfileForm(FlaskForm):
    username         = StringField('Username', render_kw={'readonly': True, 'disabled': 'disabled'})
    name             = StringField('First Name', render_kw={'readonly': True, 'disabled': 'disabled'})
    lastname         = StringField('Last Name', render_kw={'readonly': True, 'disabled': 'disabled'})
    email            = StringField('Email', validators=[DataRequired(), Email()])
    password         = PasswordField('New Password', validators=[Optional(), Length(min=6)], render_kw={'placeholder': 'Leave blank to keep current password'})
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
