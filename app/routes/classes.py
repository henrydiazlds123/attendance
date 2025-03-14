from flask          import Blueprint, jsonify, render_template, redirect, session, url_for, flash
from flask_babel    import gettext as _
from sqlalchemy.exc import IntegrityError
from app.models     import db, Classes, MeetingCenter, Organization
from app.forms      import ClassForm
from app.utils      import *

bp_classes = Blueprint('classes', __name__)

# =============================================================================================
@bp_classes.route('/', methods=['GET'])
@role_required('Admin', 'Super', 'Owner')
def classes():
    # Obtener rol, organization_id y meeting_center_id de la sesión
    role = session.get('role')
    organization_id = session['organization_id']
    meeting_center_id = get_meeting_center_id()
    
    # Inicializar la consulta básica
    query = db.session.query(
        Classes.id,
        Classes.class_name,
        Classes.short_name,
        Classes.class_code,
        Classes.class_type,
        Classes.schedule,
        Classes.is_active,
        Classes.class_color,
        Classes.organization_id,
        MeetingCenter.short_name.label('meeting_short_name')
    ).join(MeetingCenter, Classes.meeting_center_id == MeetingCenter.id)

    # Verificar si el rol es Admin
    if role == 'Admin': # Si es Admin, filtrar por meeting_center_id        
        query = query.filter(Classes.meeting_center_id == meeting_center_id)
    elif role == 'Super':# Si es Super, filtrar por organization_id y meeting_center_id       
        query = query.filter(Classes.organization_id == organization_id)
        query = query.filter(Classes.meeting_center_id == meeting_center_id)   
    elif role == 'Owner': # Si no es Admin ni Super, aplicar la lógica existente para Owner
        if not (meeting_center_id == 'all'):
            query = query.filter(Classes.meeting_center_id == meeting_center_id)
    
    # Ejecutar la consulta
    classes = query.all()

    return render_template('classes/list.html', classes=classes)


# =============================================================================================
@bp_classes.route('/new', methods=['GET', 'POST'])
@role_required('Admin', 'Super', 'Owner')
def create_class():
    # Obtener rol, organization_id y meeting_center_id de la sesión
    meeting_center_id = get_meeting_center_id()
    organization_id   = session['organization_id']
    role              = session.get('role')
    form              = ClassForm()

    if role == 'Owner':
        form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]
    else:
        form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.filter_by(id=meeting_center_id).all()]

    if (role == 'Owner' or role == 'Admin'):
        form.organization_id.choices = [(og.id, og.name) for og in Organization.query.all()]
    else:
        form.organization_id.choices = [(og.id, og.name) for og in Organization.query.filter_by(id=organization_id).all()]
    
    if form.validate_on_submit():
        new_class = Classes(
            class_name          = form.class_name.data,
            short_name          = form.short_name.data,
            class_code          = form.class_code.data,
            class_type          = form.class_type.data,
            schedule            = form.schedule.data,
            is_active           = form.is_active.data,
            class_color         = form.class_color.data,
            meeting_center_id   = form.meeting_center_id.data,
            organization_id     = form.organization_id.data
        )
        try:
            db.session.add(new_class)
            db.session.commit()
            flash(_('Class created successfully!'), 'success')
            return redirect(url_for('classes.classes'))
        except IntegrityError:
            db.session.rollback()
            flash(_('A class with this name, short name, or code already exists in the same church unit.'), 'danger')
    return render_template('/form/form.html', form=form, title=_('Create new Class'), submit_button_text=_('Create'), clas='warning')


# =============================================================================================
@bp_classes.route('/edit/<int:id>', methods=['GET', 'POST'])
@role_required('Admin', 'Super', 'Owner')
def update_class(id):
    class_instance = Classes.query.get_or_404(id)
    form           = ClassForm(obj=class_instance)
    form.meeting_center_id.choices = [(mc.id, mc.name) for mc in MeetingCenter.query.all()]
    form.organization_id.choices = [(og.id, og.name) for og in Organization.query.all()]
    
    if form.validate_on_submit():
        class_instance.class_name        = form.class_name.data
        class_instance.short_name        = form.short_name.data
        class_instance.class_code        = form.class_code.data
        class_instance.class_type        = form.class_type.data
        class_instance.schedule          = form.schedule.data
        class_instance.is_active         = form.is_active.data
        class_instance.class_color       = form.class_color.data
        class_instance.meeting_center_id = form.meeting_center_id.data
        class_instance.organization_id   = form.organization_id.data
        try:
            db.session.commit()
            flash(_('Class updated successfully!'), 'success')
            return redirect(url_for('classes.classes'))
        except IntegrityError:
            db.session.rollback()
            flash(_('A class with this name, short name, or code already exists in the same church unit.'), 'danger')
    return render_template('/form/form.html', form=form, title=_('Edit Class'), submit_button_text=_('Update'), clas='warning', backroute='classes')


# =============================================================================================
@bp_classes.route('/reset_color/<int:class_id>', methods=['POST'])
@login_required
def reset_class_color(class_id):
    class_obj = Classes.query.get_or_404(class_id)
    try:
        class_obj.class_color = "#000000"
        db.session.commit()
        return jsonify({"message": "Color restablecido con éxito."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al restablecer el color: {str(e)}"}), 500

# =============================================================================================
@bp_classes.route('/delete/<int:id>', methods=['POST'])
@role_required('Admin', 'Owner')
def delete_class(id):
    class_instance = Classes.query.get_or_404(id)
    if class_instance.attendances:
        flash(_('The class cannot be deleted because it has attendance recorded.'), 'danger')
        return redirect(url_for('classes.classes'))
    if class_instance.class_type == 'main':
        flash(_('Cannot delete a main class.'), 'warning')
        return redirect(url_for('classes.classes'))
    try:
        db.session.delete(class_instance)
        db.session.commit()
        flash(_('Class deleted successfully!'), 'success')
    except Exception as e:
        db.session.rollback()
        flash(_('Error deleting class: %(error)s') % {'error': e}, 'danger')
        
    return redirect(url_for('classes.classes'))

# =============================================================================================   
@bp_classes.route('/classes/populate/<int:id>', methods=['GET', 'POST'])
@role_required('Owner')
def populate_classes(id):
    new_meeting_center_id = id

    # Arreglo estático con las clases tipo Main
    main_classes_static = [
        {
            'class_name'     : _('Elders Quorum'),
            'short_name'     : _('Elders_Q'),
            'class_code'     : _('EQ'),
            'class_type'     : _('Main'),
            'schedule'       : '2,4',
            'is_active'      : True,
            'class_color'    : None,
            'organization_id': 2
        },
        {
            'class_name'     : _('Aaronic Priesthood'),
            'short_name'     : _('Aaronic_P'),
            'class_code'     : _('AP'),
            'class_type'     : _('Main'),
            'schedule'       : '2,4',
            'is_active'      : True,
            'class_color'    : None,
            'organization_id': 4
        },
        {
            'class_name'     : _('Relief Society'),
            'short_name'     : _('Relief_S'),
            'class_code'     : _('RS'),
            'class_type'     : _('Main'),
            'schedule'       : '2,4',
            'is_active'      : True,
            'class_color'    : '#ba8e23',
            'organization_id': 3
        },
        {
            'class_name'     : _('Young Woman'),
            'short_name'     : _('Young_W'),
            'class_code'     : _('YW'),
            'class_type'     : _('Main'),
            'schedule'       : '2,4',
            'is_active'      : True,
            'class_color'    : '#943f88',
            'organization_id': 5
        },
        {
            'class_name'     : _('Sunday School Adults'),
            'short_name'     : _('S_S_Adults'),
            'class_code'     : _('SSA'),
            'class_type'     : _('Main'),
            'schedule'       : '1,3',
            'is_active'      : True,
            'class_color'    : None,
            'organization_id': 6
        },
        {
            'class_name'     : _('Sunday School Youth'),
            'short_name'     : _('S_S_Youth'),
            'class_code'     : _('SSY'),
            'class_type'     : _('Main'),
            'schedule'       : '1,3',
            'is_active'      : True,
            'class_color'    : None,
            'organization_id': 6
        },
        {
            'class_name'     : _('Fifth Sunday'),
            'short_name'     : _('F_Sunday'),
            'class_code'     : _('FS'),
            'class_type'     : _('Main'),
            'schedule'       : '5',
            'is_active'      : True,
            'class_color'    : None,
            'organization_id': 1
        }
    ]
    try:
        # Validar si ya existen clases asociadas al nuevo Meeting Center
        existing_classes = Classes.query.filter_by(meeting_center_id=new_meeting_center_id).first()
        if existing_classes:
            flash(_('Classes already exist for this meeting center'), 'warning')
            return redirect(url_for('classes.meeting_centers'))

        # Insertar las clases del arreglo estático
        for class_data in main_classes_static:
            new_class = Classes(
                class_code        = class_data['class_code'],
                class_color       = class_data['class_color'],
                class_name        = class_data['class_name'],
                class_type        = class_data['class_type'],
                is_active         = class_data['is_active'],
                meeting_center_id = new_meeting_center_id,
                organization_id   = class_data['organization_id'],
                schedule          = class_data['schedule'],
                short_name        = class_data['short_name'],
            )
            db.session.add(new_class)

        # Confirmar los cambios en la base de datos
        db.session.commit()
        flash(_('Main classes successfully populated.'), 'success')

    except IntegrityError as ie:
        db.session.rollback()

        flash(_('Unique constraint error:  %(error)s') % {'error':str(ie)}, 'danger')
    except Exception as e:
        db.session.rollback()
        flash(_('Error duplicating main classes for new meeting center: %(error)s') % {'error':str(ie)}, 'danger')

    return redirect(url_for('classes.meeting_centers'))
