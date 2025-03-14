# app/routes/members.py
from flask            import Blueprint, redirect, render_template, request, jsonify, url_for
from datetime         import date
from app.forms.member import MemberForm
from app.models       import db, Member
from flask_babel      import gettext as _
from app.utils        import *


bp_members = Blueprint('members', __name__)


# =================================================================
@bp_members.route('/')
def list_members():
    query= Member.query

    # Obtener los valores distintos de family_head
    family_head = query.with_entities(Member.family_head).distinct().order_by(Member.family_head.asc()).all()

    return render_template('members/list.html', family_head = family_head )


# =================================================================
@bp_members.route('/api/members', methods=['GET'])
def get_members():

    page       = request.args.get('page', 1, type=int)
    per_page   = request.args.get('per_page', 25, type=int)  # Valores predeterminados
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
        'age'              : m.age(),
        'gender'           : m.gender,
        'priesthood'       : m.priesthood,
        'priesthood_office': m.priesthood_office,
        'sector'           : m.sector,
        'calling'          : m.calling,
        'time_in_ward'     : (date.today() - m.arrival_date).days  // 365 if m.arrival_date else None,
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
def update_active(member_id):
    member        = Member.query.get_or_404(member_id)
    data          = request.json
    member.active = data.get('active', member.active)
    db.session.commit()
    return jsonify({'success': True, 'active': member.active})



# =================================================================
@bp_members.route('/add', methods=['GET', 'POST'])
def add_member():
    form = MemberForm()
    if request.method == 'POST':
        if form.validate_on_submit():
          new_member = Member(
              full_name=request.form['full_name'],
              preferred_name=request.form['preferred_name'],
              birth_date=request.form['birth_date'],
              gender=request.form['gender'],
              priesthood=request.form['priesthood'],
              priesthood_office=request.form['priesthood_office'],
              address=request.form['address'],
              city=request.form['city'],
              sector=request.form['sector'],
              lat=request.form.get('lat', type=float),
              lon=request.form.get('lon', type=float),
              fix_address='fix_address' in request.form,
              excluded='excluded' in request.form,
              new='new' in request.form,
              calling=request.form['calling'],
              arrival_date=request.form['arrival_date'],
              moved_out='moved_out' in request.form,
              active='active' in request.form,
              status=request.form['status'],
              category=request.form['category'],
              short_name=request.form['short_name']
          )
          db.session.add(new_member)
          db.session.commit()
          return redirect(url_for('members.list_members'))
    return render_template('members/add.html', form=form)


# =================================================================
@bp_members.route('/pivot')
def pivot_table():
    # Traducir múltiples categorías en el servidor
    cols_translated = [_('Condition')]
    rows_translated = [_('Gender'),_('Category'),_('Priesthood'), _('Office')]
    # Pasar el JSON a la plantilla
    return render_template('members/pivot.html', rows_translated=rows_translated, cols_translated=cols_translated)


# =================================================================
@bp_members.route('/api', methods=['GET'])
def pivot_data():
    # members = Member.query.filter_by(excluded=False).all()
    members = Member.query.all()

    members_data = []
    for member in members:
        age = get_age(member.birth_date)
        years_in_unit = get_years_in_unit(member.arrival_date)

        member_data = {
            _('Name'): member.preferred_name or "-",
            _('Condition'): _('Active') if member.active else _('Inactive'),
            _('Sex'): _('Female') if member.gender == 'F' else _('Male'),
            _('Marital Status'): _('Single') if member.marital_status == 'Soltero(a)' else _('Married'),
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