# app/forms/clase.py
from flask              import session
from flask_wtf          import FlaskForm
from flask_babel        import lazy_gettext as _l, _
from wtforms.validators import Regexp, DataRequired, Length
from wtforms.validators import DataRequired, Length
from wtforms            import BooleanField, StringField, SelectField

   
#==================================================================================================    
class ClassForm(FlaskForm):
    class_name      = StringField(_l('Class Name'), validators=[DataRequired(), Length(max=50)])
    short_name      = StringField(_l('Short Name'), validators=[DataRequired(), Length(max=20)])
    class_code      = StringField(_l('Class Code'), validators=[DataRequired(), Length(max=10)])
    class_type      = SelectField(_l('Class Type'), choices=[], default=_l('Extra'))
    organization_id = SelectField(_l('Organization'), coerce=int, validators=[DataRequired()])
    schedule        = StringField(_l('Schedule'), validators=[Length(max=10)])
    is_active       = BooleanField(_l('Is Active?'), default=True)
    class_color     = StringField(
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
            role = session['role']
            is_owner = role == 'Owner'
            is_admin = role == 'Admin'

            # Deshabilitar campos si no es Owner y la clase es Main
            if not is_owner and self.class_type.data == 'Main':
                for field in [
                    self.meeting_center_id,
                    self.class_name,
                    self.short_name,
                    self.class_code,
                    self.class_type,
                    self.schedule,
                    self.is_active,
                    self.organization_id
                ]:
                    field.render_kw = {'disabled': 'disabled'}
                self.meeting_center_id.data = session.get('meeting_center_id')

            # Configurar opciones de class_type según el rol
            self.class_type.choices = [('Main', _('Main')), ('Extra', _('Extra'))] if is_owner else [('Extra', _('Extra'))]

            # Deshabilitar class_type y meeting_center_id si no es Owner
            if not is_owner:
                for field in [self.class_type, self.meeting_center_id]:
                    field.render_kw = {'disabled': 'disabled'}

            # Deshabilitar organization_id si no es Owner ni Admin
            if not (is_owner or is_admin):
                self.organization_id.render_kw = {'disabled': 'disabled'}

