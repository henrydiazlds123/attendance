# app/routes/members.py
from flask            import Blueprint, redirect, render_template, request, jsonify, url_for, current_app
from datetime         import date
from app.forms        import MemberForm, MemberEditForm
from app.models       import db, Member
from flask_babel      import gettext as _
from app.utils        import *


bp_members = Blueprint('members', __name__)


# =================================================================
@bp_members.route('/')
@role_required('Admin', 'Owner')
def list_members():
    query= Member.query

    # Obtener los valores distintos de family_head
    family_head = query.with_entities(Member.family_head).distinct().order_by(Member.family_head.asc()).all()

    return render_template('members/list.html', family_head=family_head )


# =================================================================
@bp_members.route('/new', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def add_member():
    form = MemberForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            # Recogemos los datos del formulario
            preferred_name = request.form['preferred_name']
            short_name     = request.form['short_name']
            
            # Creamos un nuevo miembro
            new_member = Member(
                full_name         = request.form['full_name'],
                preferred_name    = preferred_name if preferred_name else None,  # Si está vacío, lo dejamos como None para calcularlo luego
                short_name        = short_name if short_name else None,  # Si está vacío, lo dejamos como None para calcularlo luego
                birth_date        = request.form['birth_date'],
                gender            = request.form['gender'],
                priesthood        = request.form['priesthood'],
                priesthood_office = request.form['priesthood_office'],
                address           = request.form['address'],
                city              = request.form['city'],
                state             = request.form['state'],
                zip_code          = request.form['zip_code'],
                sector            = request.form['sector'],
                lat               = request.form.get('lat', type=float),
                lon               = request.form.get('lon', type=float),
                fixed_address     = request.form['fixed_address'],
                excluded          = 'excluded' in request.form,
                calling           = request.form['calling'],
                arrival_date      = request.form['arrival_date'],
                active            = 'active' in request.form,
                status            = request.form['status'],
                category          = request.form['category']
            )

            # Si preferred_name o short_name están vacíos, calculamos los nombres
            if not new_member.preferred_name or not new_member.short_name:
                new_member._calculate_names()

            # Guardamos el nuevo miembro en la base de datos
            db.session.add(new_member)
            db.session.commit()

            # Redirigimos a la lista de miembros
            return redirect(url_for('members.list_members'))
    
    # Renderizamos el formulario
    return render_template('/form/member_form.html', form=form, title=_('Create new Member'), submit_button_text=_('Create'), clas='warning')


# =================================================================
@bp_members.route('/edit/<int:member_id>', methods=['GET', 'POST'])
@role_required('Admin', 'Owner')
def edit_member(member_id):
    member = Member.query.get_or_404(member_id)
    form   = MemberEditForm(obj=member)  # Prellenar el formulario con los datos del miembro

    if request.method == 'POST' and form.validate_on_submit():
        member.full_name         = request.form['full_name']
        member.preferred_name    = request.form['preferred_name']
        member.birth_date        = request.form['birth_date']
        member.gender            = request.form['gender']
        member.priesthood        = request.form['priesthood']
        member.priesthood_office = request.form['priesthood_office']
        member.address           = request.form['address']
        member.city              = request.form['city']
        member.state             = request.form['state']
        member.zip_code          = request.form['zip_code']
        member.sector            = request.form['sector']
        member.lat               = request.form.get('lat', type=float)
        member.lon               = request.form.get('lon', type=float)
        member.fixed_address     = request.form['fixed_address']
        member.excluded          = 'excluded' in request.form
        member.calling           = request.form['calling']
        member.arrival_date      = request.form['arrival_date']
        member.moved_out         = 'moved_out' in request.form
        member.active            = 'active' in request.form
        member.status            = request.form['status']
        member.category          = request.form['category']
        member.short_name        = request.form['short_name']
        member.family_head       = request.form['family_head']

        db.session.commit()
        return redirect(url_for('members.list_members'))

    return render_template('/form/member_form.html', form=form, title=_('Edit Member'), submit_button_text=_('Save'), clas='warning', member=member)


# =================================================================
@bp_members.route('/profile/<int:member_id>')
@role_required('Admin', 'Owner')
def profile(member_id):
    member = Member.query.get_or_404(member_id)
    google_maps_api_key = current_app.config.get("GOOGLE_MAPS_API_KEY", "default-google-key")

    # Calcular la edad
    today = datetime.today()
    birth_date = member.birth_date
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    return render_template('members/profile.html', member=member, age=age, google_maps_api_key=google_maps_api_key)


# =================================================================
@bp_members.route('/api/members', methods=['GET'])
@role_required('Admin', 'Owner')
def get_members():

    all = len(Member.query.all())
    print(f"All: {all}")

    page       = request.args.get('page', 1, type=int)
    per_page   = request.args.get('per_page', all, type=int)  # Valores predeterminados
    print(f"🔍 Parámetros recibidos en el servidor -> page: {page}, per_page: {per_page}")
    
    query = Member.query
    
    # Filtros
    family            = request.args.get('family')
    name              = request.args.get('name')
    gender            = request.args.get('gender')
    category          = request.args.get('category')
    sector            = request.args.get('sector')
    priesthood        = request.args.get('priesthood')
    priesthood_office = request.args.get('priesthood_office')
    has_calling       = request.args.get('has_calling')
    active            = request.args.get('condition')
    
    if family:
        query = query.filter(Member.family_head.ilike(f'%{family}%'))
    if name:
        query = query.filter(Member.short_name.ilike(f'%{name}%'))
    if gender:
        query = query.filter(Member.gender == gender)
    if category:
        query = query.filter(Member.birth_date != None)
        query = query.filter(get_category_filter(category))
    if sector:
        query = query.filter(Member.sector.ilike(f'%{sector}%'))
    if priesthood:
        query = query.filter(Member.priesthood.ilike(f'%{priesthood}%'))
    if priesthood_office:
        query = query.filter(Member.priesthood_office.ilike(f'%{priesthood_office}%'))
    if active == 'yes':
        query = query.filter(Member.active == True)
    if active == 'no':
        query = query.filter(Member.active == False)
    if has_calling == 'yes':
        query = query.filter(Member.calling.isnot(None))
    elif has_calling == 'no':
        query = query.filter(Member.calling.is_(None))

    # Obtener el total de miembros filtrados **antes de paginar**
    members_count = query.count()
    
    # Ordenamiento
    query = query.order_by(Member.family_head, Member.birth_date.asc(), Member.gender.desc())

    # Paginación
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    members    = pagination.items
    
    data = [{
        'id'               : m.id,
        'short_name'       : m.short_name,
        'preferred_name'   : m.preferred_name,
        'age'              : m.age(),
        'gender'           : m.gender,
        'priesthood'       : m.priesthood,
        'priesthood_office': m.priesthood_office,
        'sector'           : m.sector,
        'calling'          : _(m.calling),
        'time_in_ward'     : "0y-"+str(((date.today() - m.arrival_date).days)//30)+"m" if m.arrival_date and (date.today() - m.arrival_date).days < 365 else (date.today() - m.arrival_date).days // 365 if m.arrival_date else None,
        'active'           : m.active,
        'category'         : get_category(m.age())
    } for m in members]
    
    return jsonify({
                'members'     : data,
                'count'       : pagination.total,
                'page'        : pagination.page,
                'per_page'    : pagination.per_page,
                'total_pages' : pagination.pages,
                'members_count':members_count
                })

# =================================================================
@bp_members.route('/api/members/<int:member_id>/active', methods=['PATCH'])
@role_required('Admin', 'Owner')
def update_active(member_id):
    member        = Member.query.get_or_404(member_id)
    data          = request.json
    member.active = data.get('active', member.active)
    db.session.commit()
    return jsonify({'success': True, 'active': member.active})


# =================================================================
@bp_members.route('/pivot')
@role_required('Admin', 'Owner')
def pivot_table():
    # Traducir múltiples categorías en el servidor
    cols_translated = [_('Condition')]
    rows_translated = [_('Gender'),_('Category'),_('Priesthood'), _('Office')]
    # Pasar el JSON a la plantilla
    return render_template('members/pivot.html', rows_translated=rows_translated, cols_translated=cols_translated)


# =================================================================
@bp_members.route('/pivot/api', methods=['GET'])
@role_required('Admin', 'Owner')
def pivot_data():
    members = Member.query.all()
    members_data = []
    for member in members:
        age = get_age(member.birth_date)
        years_in_unit = get_years_in_unit(member.arrival_date)

        member_data = {
            _('Name'): member.preferred_name or "-",
            _('Condition'): _('Active') if member.active else _('Inactive'),
            _('Sex'): _('Female') if member.gender == 'F' else _('Male'),
            _('Marital Status'): member.marital_status,
            _('Age'): age,
            _('Category'): get_category(age),
            _('Priesthood'): member.priesthood or '-',
            _('Office'): member.priesthood_office or '-',
            _('Area'): member.sector or '-',
            _('Time in unit'): years_in_unit,
            _('Calling'): _('has calling') if member.calling else _('No callings')
        }
        members_data.append(member_data)
    return jsonify(members_data)  # ✅ Devuelve JSON correctamente