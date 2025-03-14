from flask                   import Blueprint, render_template, redirect, session, url_for, flash
from flask_babel             import gettext as _
from sqlalchemy              import asc
from app.models                  import db, User, MeetingCenter, Organization
from app.forms                   import UserForm, EditUserForm, ResetPasswordForm, ProfileForm
from app.utils                   import *

bp_users = Blueprint('user', __name__)

# =============================================================================================
@bp_users.route('/')
@role_required('Admin', 'Super', 'Owner')
def users():
    role              = session.get('role')
    meeting_center_id = get_meeting_center_id()
    organization_id   = session.get('organization_id')  # Agregamos la organización del usuario actual
    admin_count       = User.query.filter_by(role='Admin').count()
    print(f"Users Meeting Center ID: {meeting_center_id}")  # Debugging output

    query = db.session.query(
        User.id,
        User.username,
        User.email,
        User.role,
        MeetingCenter.short_name.label('meeting_short_name'),
        Organization.name.label('organization_name')
    ).join(MeetingCenter, User.meeting_center_id == MeetingCenter.id) \
     .join(Organization, User.organization_id == Organization.id)

    if role == 'Owner': # El Owner ve todos si el meeting_center_id es 'all'       
        if meeting_center_id != 'all': 
            query = query.filter(User.meeting_center_id == meeting_center_id)
        query = query.filter((User.role != 'Owner') | (User.username == session.get('username')))
    elif role == 'Super': # Super ve solo usuarios de su organización        
        query = query.filter(User.organization_id == organization_id).filter((User.role != 'Owner') | (User.username == session.get('username')))
    elif role == 'Admin': # Admin ve solo usuarios de su propio Meeting Center, excluyendo Owners        
        query = query.filter(User.meeting_center_id == meeting_center_id).filter(User.role != 'Owner')
    else:
        # Usuario regular solo ve su propio usuario
        query = db.session.query(
            User.id,
            User.username,
            User.email,
            User.role,
            MeetingCenter.short_name.label('meeting_short_name'),
            Organization.name.label('organization_name')
        ).join(MeetingCenter, User.meeting_center_id == MeetingCenter.id) \
         .join(Organization, User.organization_id == Organization.id) \
         .filter(User.username == session.get('username'))

    users = query.order_by(asc(User.meeting_center_id), asc(User.organization_id), asc(User.role)).all()

    return render_template('users/list.html', users=users, admin_count=admin_count)


# =============================================================================================
@bp_users.route('/new', methods=['GET', 'POST'])
@role_required('Admin', 'Super', 'Owner')
def create_user():

    form                           = UserForm()
    form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]
    form.organization_id.choices   = [(og.id, og.translated_name) for og in Organization.query.all()]

    if form.validate_on_submit():
        user = User(
            username         =form.username.data, 
            email            =form.email.data, 
            name             =form.name.data,
            lastname         =form.lastname.data,
            role             =form.role.data,
            meeting_center_id=form.meeting_center_id.data,
            organization_id  =form.organization_id.data,
            is_active        =form.is_active.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('user.users'))
    return render_template('/form/form.html', form=form, title=_('New User'), submit_button_text=_('Create'), clas='warning')


# =============================================================================================
@bp_users.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def update_user(id):
    user                           = User.query.get_or_404(id)
    form                           = EditUserForm(obj=user)
    form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]
    form.organization_id.choices   = [(og.id, og.translated_name) for og in Organization.query.all()]

    if form.validate_on_submit():
        user.username          = form.username.data
        user.email             = form.email.data
        user.name              = form.name.data
        user.lastname          = form.lastname.data
        user.role              = form.role.data
        user.meeting_center_id = form.meeting_center_id.data
        user.is_active         = form.is_active.data

        db.session.commit()
        flash(_('User updated successfully.'), 'success')
        return redirect(url_for('user.users'))
    return render_template('/form/form.html',
                           form               = form,
                           title              = _('Edit User'),
                           submit_button_text = _('Update'),
                           clas               = 'warning')


# =============================================================================================
@bp_users.route('/delete/<int:id>', methods=['POST'])
@role_required('Admin', 'Super', 'Owner')  # Solo los admins pueden acceder a esta ruta
def delete_user(id):
    user_to_delete = User.query.get_or_404(id)
    current_user_id = session.get('user_id')
    current_user_role = session.get('role')

    # Contar cuántos admins existen en total
    admin_count = User.query.filter_by(role='Admin').count()

    # Verificar si el usuario actual es Owner
    if current_user_role == 'Owner':
        if user_to_delete.role == 'Admin' and admin_count <= 1:
            flash(_('Cannot delete last admin.'), 'danger')
            return redirect(url_for('user.users'))
        
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(_('User deleted successfully'), 'success')
        return redirect(url_for('user.users'))

    # Los Admin no pueden eliminar a otros Admin
    if user_to_delete.role == 'Admin':
        flash(_('You cannot delete another administrator.'), 'danger')
        return redirect(url_for('user.users'))

    # Los Admin pueden eliminar a un usuario común (User)
    if current_user_id == user_to_delete.id:  # Permitir que un admin se elimine a sí mismo
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(_('You have successfully eliminated yourself.'), 'success')
        return redirect(url_for('auth.login'))  # Redirigir a la página de login

    db.session.delete(user_to_delete)
    db.session.commit()
    flash(_('User deleted successfully'), 'success')
    return redirect(url_for('user.users'))


# =============================================================================================
@bp_users.route('/<int:id>/reset_password', methods=['GET', 'POST'])
def reset_password(id):
    user = User.query.get_or_404(id)
    form = ResetPasswordForm()

    if form.validate_on_submit():
        if not user.check_password(form.current_password.data):
            flash(_('Current password is incorrect.'), 'danger')
            return render_template('/form/form.html', 
                                   form               = form,
                                   title              = "Reset Password",
                                   submit_button_text = "Update",
                                   clas               = "danger")

        user.set_password(form.new_password.data)
        db.session.commit()
        flash(_('Password updated successfully.'), 'success')
        return redirect(url_for('user.users'))

    return render_template('/form/form.html', 
                           form               = form,
                           title              = "Change Password",
                           submit_button_text = "Update",
                           clas               = "danger")


# =============================================================================================
@bp_users.route('/<int:id>/promote', methods=['POST'])
@role_required('Owner', 'Admin')
def promote_to_super(id):
    user = User.query.get_or_404(id)
    if user.role =='Super':
        flash(_('The user is already an Super User.'), 'info')
    else:
        user.role = 'Super'
        db.session.commit()
        # flash(f'El usuario {user.username} ha sido promovido a administrador.', 'success')
        flash(_('User %(username)s has been promoted to Super User.') % {'username': user.username}, 'success')
    return redirect(url_for('user.users'))

# =============================================================================================
@bp_users.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()

    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

    if form.validate_on_submit():
        # Verificar si el email ya existe y no pertenece al usuario actual
        if User.query.filter(User.email == form.email.data, User.id != user.id).first():
            flash('Email already in use by another account.', 'danger')
            return redirect(url_for('profile'))

        user.email = form.email.data
        #user.name = form.name.data
        #user.lastname = form.lastname.data

        # Cambiar la contraseña si se ingresó una nueva
        if form.password.data:
            user.set_password(form.password.data)

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('user.profile'))

    # Prellenar el formulario con los datos actuales del usuario
    form.username.data = user.username
    form.email.data    = user.email
    form.name.data     = user.name
    form.lastname.data = user.lastname

    return render_template('/form/form.html',
                           form=form,
                           title=_('Edit User Profile'),
                           submit_button_text=_('Update Profile'),
                           clas='warning'
                           )