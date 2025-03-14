from flask       import Blueprint, jsonify, render_template, redirect, request, session, url_for, flash
from flask_babel import gettext as _
from app.models  import db, Classes, MeetingCenter, Setup
from app.forms   import MeetingCenterForm
from app.utils   import *

bp_meeting_center = Blueprint('meeting_center', __name__)


# =============================================================================================
# CRUD para Meeting Centers
@bp_meeting_center.route('/', methods=['GET', 'POST'])
@role_required('Owner')
def meeting_centers():
    meeting_centers    = MeetingCenter.query.all()
    main_classes_exist = {mc.id: Classes.query.filter_by(meeting_center_id=mc.id, class_type='Main').count() > 0 for mc in meeting_centers}
    return render_template('meeting_centers/list.html', meeting_centers=meeting_centers, main_classes_exist=main_classes_exist)


# =============================================================================================
@bp_meeting_center.route('/new', methods=['GET', 'POST'])
@role_required('Owner')
def create_meeting_center():
    form = MeetingCenterForm()
    if form.validate_on_submit():
        new_center     = MeetingCenter(
            unit_number=form.unit_number.data,
            name       =form.name.data,
            short_name =form.short_name.data,
            city       =form.city.data,
            start_time =form.start_time.data,
            end_time   =form.end_time.data
        )
        db.session.add(new_center)
        db.session.commit()
        flash(_('Meeting center created successfully!'), 'success')
        return redirect(url_for('meeting_center.meeting_centers'))
    return render_template('/form/form.html', form=form, title=_('Create new Meeting center'), submit_button_text=_('Create'), clas='warning')


# =============================================================================================
@bp_meeting_center.route('/edit/<int:id>', methods=['GET', 'POST'])
@role_required('Owner')
def update_meeting_center(id):
    meeting_center = MeetingCenter.query.get_or_404(id)
    form           = MeetingCenterForm(obj=meeting_center)
    if form.validate_on_submit():
        form.populate_obj(meeting_center)
        db.session.commit()
        flash(_('Meeting Center updated successfully.'), 'success')
        return redirect(url_for('meeting_center.meeting_centers'))
    return render_template('/form/form.html', form=form, title=_('Edit Meeting Center'), submit_button_text=_('Update'), clas='warning')


# =============================================================================================
@bp_meeting_center.route('/delete/<int:id>', methods=['POST'])
@role_required('Owner')
def delete_meeting_center(id):
    meeting_center = MeetingCenter.query.get_or_404(id)
    if meeting_center.attendances:
        flash(_('The meeting center cannot be deleted because it has registered attendance.'), 'danger')
        return redirect(url_for('meeting_center.meeting_centers'))
    
    db.session.delete(meeting_center)
    db.session.commit()
    flash(_('Meeting Center successfully removed.'), 'success')
    return redirect(url_for('meeting_center.meeting_centers'))


# =============================================================================================
@bp_meeting_center.route('/api')
@login_required
def get_meeting_centers():
    meeting_centers = MeetingCenter.query.order_by(MeetingCenter.name).all()
    return jsonify([{"id": mc.id, "name": mc.name} for mc in meeting_centers])


# =============================================================================================
@bp_meeting_center.route('/set', methods=['POST'])
@login_required
def set_meeting_center():
    data = request.get_json()
    print(f"📌 Datos recibidos en /set: {data}")
    
    meeting_center_id = data.get('meeting_center_id')
    print(f"Before Update - Meeting Center ID: {session.get('meeting_center_id')}")  # Antes de actualizar
    session['meeting_center_id'] = meeting_center_id
    print(f"After Update - Meeting Center ID: {session.get('meeting_center_id')}")  # Después de actualizar

    # Aquí actualizamos el `SelectedMeetingCenterId` si el rol es 'Owner'
    if session.get('role') == 'Owner':
        
        if meeting_center_id:
            # Verificamos si ya existe la clave en Setup
            setup_entry = Setup.query.filter_by(key='SelectedMeetingCenterId', meeting_center_id=1).first()

            if setup_entry:
                setup_entry.value = meeting_center_id  # Actualizamos el valor
            else:
                # Si no existe, creamos un nuevo registro
                setup_entry = Setup(
                    key='SelectedMeetingCenterId',
                    value=meeting_center_id,
                    meeting_center_id=1  # Usamos 1 como valor por defecto
                )
                db.session.add(setup_entry)
            
            db.session.commit()


    if meeting_center_id == 'all':
        session['meeting_center_name'] = _('All Meeting Centers')
        session['meeting_center_number'] = 'N/A'
    else:
        meeting_center = MeetingCenter.query.get(meeting_center_id)
        if meeting_center:
            session['meeting_center_name'] = meeting_center.name
            session['meeting_center_number'] = meeting_center.unit_number
        else:
            session['meeting_center_name'] = _('Unknown')
            session['meeting_center_number'] = 'N/A'

    return jsonify({
        "meeting_center_id"    : session['meeting_center_id'],
        "meeting_center_name"  : session['meeting_center_name'],
        "meeting_center_number": session['meeting_center_number']
    })
