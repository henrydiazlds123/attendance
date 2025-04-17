from flask       import Blueprint, render_template, redirect, request, session, url_for, flash
from flask_babel import gettext as _
from app.models  import User, MeetingCenter
from app.utils   import *

bp_auth = Blueprint('auth', __name__)

# =============================================================================================
@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next')

    if request.method == 'POST':
        username    = request.form['username']
        password    = request.form['password']
        remember_me = request.form.get('remember_me') == 'on'

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            meeting_center = MeetingCenter.query.get(user.meeting_center_id)
            session['user_id']         = user.id
            session['user_name']       = user.name
            session['username']        = user.username
            session['user_lastname']   = user.lastname
            session['user_email']      = user.email
            session['role']            = user.role  # Guarda el rol del usuario
            session['organization_id'] = user.organization_id

            # Aquí es donde cambiamos el comportamiento:
            # Si el 'Owner' ya seleccionó un 'meeting_center_id', usarlo
            if user.role == 'Owner':
                selected_meeting_center_id = session.get('meeting_center_id', 'all')  # Traer el valor de la sesión
                if selected_meeting_center_id == 'all':
                    session['meeting_center_name']   = _('All Meeting Centers')
                    session['meeting_center_number'] = 'N/A'
                else:
                    meeting_center = MeetingCenter.query.get(selected_meeting_center_id)
                    if meeting_center:
                        session['meeting_center_name']   = meeting_center.name
                        session['meeting_center_number'] = meeting_center.unit_number
                    else:
                        session['meeting_center_name']   = _('Unknown')
                        session['meeting_center_number'] = 'N/A'
            else:
                session['meeting_center_id']     = meeting_center.id
                session['meeting_center_name']   = meeting_center.name
                session['meeting_center_number'] = meeting_center.unit_number

            # Si "Remember Me" está marcado, guarda la cookie
            response = redirect(next_url or url_for('attendance.attendance_report'))
            if remember_me:
                response.set_cookie('remember_me', str(user.id), max_age=2*24*60*60)  # 30 días
            return response

        flash(_('Invalid credentials. Please check your username and password.'), 'danger')

    return render_template('auth/login.html')



# =============================================================================================
@bp_auth.route('/logout')
def logout():
    session.clear()
    response = redirect(url_for('auth.login'))
    response.delete_cookie('remember_me')  # Elimina la cookie al cerrar sesión
    flash(_('Logout successful!'), 'success')
    return response


# =============================================================================================
@bp_auth.route('/reset_name')
def reset_name():
    """Renderiza una página para mostrar el nombre almacenado y borrarlo con confirmación."""
    return render_template('reset_name.html')


# =============================================================================================
@bp_auth.route('/')
def index():
    #return render_template('index.html')
    return redirect('/agenda/new', code=302)