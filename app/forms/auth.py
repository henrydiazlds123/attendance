# app/forms/auth.py
from flask_wtf          import FlaskForm
from flask_babel        import lazy_gettext as _l, _
from wtforms.validators import DataRequired, Length
from wtforms.validators import DataRequired, Length, EqualTo
from wtforms            import PasswordField
   

#==================================================================================================
class ResetPasswordForm(FlaskForm):
    current_password = PasswordField(_l('Current Password'), validators=[DataRequired()])
    new_password     = PasswordField(_l('New Password'), validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(_l('Confirm New Password'), validators=[DataRequired(), EqualTo('new_password', message= _l('Passwords must match'))])
    
    
