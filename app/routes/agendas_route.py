# app/routes/agenda.py
from datetime import datetime, timedelta
from flask       import Blueprint, flash, jsonify, render_template, redirect, request, url_for
from app.forms import HymnForm, AgendaForm
from app.models  import db, Agenda, Bishopric, Member, SelectedHymns, WardAnnouncements, Speaker, WardBusiness, Hymns, MeetingCenter
from sqlalchemy.orm import joinedload
from flask_babel import gettext as _
from app.utils      import *

bp_agenda = Blueprint('agenda', __name__)


def get_agenda_by_date(date):
    return Agenda.query.options(
        joinedload(Agenda.prayers),
        joinedload(Agenda.announcements),
        joinedload(Agenda.hymns),
        joinedload(Agenda.director),
        joinedload(Agenda.presider),
    ).filter_by(sunday_date=date).first()

def get_hymns_by_date(date):
    return SelectedHymns.query.filter_by(sunday_date=date).all()

def get_speakers_by_date(date):
    return Speaker.query.filter_by(sunday_date=date).all()

# =============================================================================================
@bp_agenda.route('/new', methods=['GET', 'POST'])
def new_agenda():
    date = request.args.get('date')
    print(date)
    form = AgendaForm()

    # Poblar choices de la base de datos
    form.director_id.choices          = [(b.id, b.member.preferred_name) for b in Bishopric.query.all()]
    form.presider_id.choices          = [(b.id, b.member.preferred_name) for b in Bishopric.query.all()]
    form.meeting_center_id.choices    = [(m.id, m.name) for m in MeetingCenter.query.all()]
    hymns                             = Hymns.query.all()
    hymn_choices                      = [(h.number, h.title) for h in hymns]
    form.opening_hymn_id.choices      = hymn_choices
    form.sacrament_hymn_id.choices    = hymn_choices
    form.intermediate_hymn_id.choices = hymn_choices
    form.closing_hymn_id.choices      = hymn_choices

    if request.method == 'POST':

        if form.validate_on_submit():
            # Crear agenda
            agenda = Agenda(
                sunday_date          = form.sunday_date.data,
                meeting_center_id    = form.meeting_center_id.data,
                director_id          = form.director_id.data,
                presider_id          = form.presider_id.data,
                opening_prayer       = form.opening_prayer.data,
                closing_prayer       = form.closing_prayer.data,
                opening_hymn_id      = form.opening_hymn_id.data,
                sacrament_hymn_id    = form.sacrament_hymn_id.data,
                intermediate_hymn_id = form.intermediate_hymn_id.data,
                closing_hymn_id      = form.closing_hymn_id.data
            )
            db.session.add(agenda)

            # Oradores
            for speaker_form in form.speakers:
                if speaker_form.speaker_name.data:  # Accede al campo específico
                    speaker = Speaker(name=speaker_form.speaker_name.data, agenda=agenda)
                    db.session.add(speaker)

            # Anuncios
            for announcement_form in form.announcements:  # Itera sobre los formularios
                if announcement_form.announcement_text.data:  # Accede al campo específico
                    announcement = WardAnnouncements(
                        text=announcement_form.announcement_text.data,
                        agenda=agenda
                    )
                    db.session.add(announcement)

            # Asuntos de barrio
            for business_form in form.business:  # Itera sobre los formularios
                if business_form.text.data:  # Accede al campo específico
                    business = WardBusiness(text=business_form.text.data, agenda=agenda)
                    db.session.add(business)

            db.session.commit()
            flash('Agenda created successfully!', 'success')
            return redirect(url_for('bp_agenda.new_agenda'))
        
        elif request.method == 'GET' and date:
            existing_agenda = get_agenda_by_date(date)
            if existing_agenda:
                # Precargar campos simples
                form.director_id.data = existing_agenda.director_id
                form.presider_id.data = existing_agenda.presider_id
                form.opening_prayer.data = existing_agenda.opening_prayer
                form.closing_prayer.data = existing_agenda.closing_prayer
                form.meeting_center_id.data = existing_agenda.meeting_center_id

                # Precargar himnos
                for hymn in existing_agenda.hymns:
                    hymn_form = HymnForm()
                    hymn_form.hymn_id.choices = form.hymns.form.hymn_id.choices
                    hymn_form.hymn_id.data = hymn.hymn_id
                    hymn_form.type.data = hymn.type
                    form.hymns.append_entry(hymn_form)

                # Precargar anuncios
                for announcement in existing_agenda.announcements:
                    form.announcements.append_entry({'announcement': announcement.announcement})

                # Precargar asuntos de barrio
                for business in existing_agenda.business_items:
                    form.business.append_entry({'business_item': business.business_item})

                # Precargar oradores
                for speaker in existing_agenda.speakers:
                    form.speakers.append_entry({
                        'name': speaker.name,
                        'topic': speaker.topic
                    })

    return render_template('agendas/new_agenda.html', form=form)


# =============================================================================================
@bp_agenda.route('api')
def api_get_agenda():
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'Missing date parameter'}), 400

    # Buscar la agenda por fecha
    agenda = get_agenda_by_date(date)

    # Si no existe una agenda, inicializar un diccionario vacío
    if not agenda:
        agenda_data = {
            'director_id': None,
            'presider_id': None,
            'opening_prayer': None,
            'closing_prayer': None,
            'hymns': [],
            'announcements': [],
            'business': [],
            'prayers': [],
        }
    else:
        # Formatear los datos de la agenda existente
        agenda_data = {
            'director_id': agenda.director_id,
            'presider_id': agenda.presider_id,
            'opening_prayer': agenda.opening_prayer,
            'closing_prayer': agenda.closing_prayer,
            'hymns': [
                {
                    'music_director'      : hymn.music_director,
                    'pianist'             : hymn.pianist,
                    'opening_hymn_id'     : hymn.opening_hymn_id,
                    'sacrament_hymn_id'   : hymn.sacrament_hymn_id,
                    'intermediate_hymn_id': hymn.intermediate_hymn_id,
                    'closing_hymn_id'     : hymn.closing_hymn_id,
                }
                for hymn in agenda.hymns
            ],
            'announcements': [
                {'id': a.id, 'content': a.content}
                for a in agenda.announcements
            ],
            'business': [
                {'id': b.id, 'content': b.content}
                for b in agenda.ward_business
            ],
            'prayers': [
                {'id': p.id, 'type': p.type, 'name': p.name}
                for p in agenda.prayers
            ],
        }

    # Buscar himnos, oradores y otros datos relacionados con la fecha
    hymns_for_date = get_hymns_by_date(date)
    speakers_for_date = get_speakers_by_date(date)

    # Agregar los himnos y oradores a la respuesta
    agenda_data['hymns'].extend([
        {
            'music_director'      : hymn.music_director,
            'pianist'             : hymn.pianist,
            'opening_hymn_id'     : hymn.opening_hymn_id,
            'sacrament_hymn_id'   : hymn.sacrament_hymn_id,
            'intermediate_hymn_id': hymn.intermediate_hymn_id,
            'closing_hymn_id'     : hymn.closing_hymn_id,
        }
        for hymn in hymns_for_date
    ])

    agenda_data['speakers'] = [
        {
            'youth_speaker_id': speaker.youth_speaker_id,
            'youth_topic': speaker.youth_topic,
            'speaker_1_id': speaker.speaker_1_id,
            'topic_1': speaker.topic_1,
            'speaker_2_id': speaker.speaker_2_id,
            'topic_2': speaker.topic_2,
            'speaker_3_id': speaker.speaker_3_id,
            'topic_2': speaker.topic_2
        }
        for speaker in speakers_for_date
    ]

    # Devolver la respuesta
    return jsonify(agenda_data)




@bp_agenda.route('/test', methods=['GET', 'POST'])
def agenda():
    role = session.get('role', 'Music')

    #meeting_center_id = get_meeting_center_id()
    meeting_center_id = session.get('meeting_center_id', 1)  # Asegúrate de asignar el ID del centro de reunión adecuado

    today = datetime.today()

    active_members = Member.query.filter(
        Member.active == True,
        Member.meeting_center_id == meeting_center_id,
        Member.birth_date.isnot(None)
    ).order_by(Member.preferred_name)

    youth_cutoff  = today.replace(year=today.year - 11)
    senior_cutoff = today.replace(year=today.year - 17)

    youth_members = active_members.filter(
        Member.birth_date.between(senior_cutoff, youth_cutoff)
    ).all()

    adult_members = active_members.filter(
        Member.birth_date < senior_cutoff
    ).all()

    # Convertir los objetos Member a un formato serializable
    youth_members_serializable = [
        {"preferred_name": member.preferred_name, "id": member.id}  # Añadir otros campos necesarios
        for member in youth_members
    ]

    adult_members_serializable = [
        {"preferred_name": member.preferred_name, "id": member.id}  # Añadir otros campos necesarios
        for member in adult_members
    ]
    
    # GET
    today        = datetime.today()
    start_date   = datetime(today.year, (today.month - 1) // 3 * 3 + 1, 1)
    end_date     = start_date + timedelta(days=90)
    sundays_data = get_sundays(start_date, end_date)

    saved_speakers = Speaker.query.filter_by(meeting_center_id=meeting_center_id).all()
    speakers_data = {}

    # Recopilar los oradores guardados en la base de datos
    for entry in saved_speakers:
        date_str = entry.sunday_date.strftime('%Y-%m-%d')
        speakers_data[date_str] = {
            "Youth Speaker": entry.youth_speaker_id,
            "Youth Topic"  : entry.youth_topic,
            "1st Speaker"  : entry.speaker_1_id,
            "1st Topic"    : entry.topic_1,
            "2nd Speaker"  : entry.speaker_2_id,
            "2nd Topic"    : entry.topic_2,
            "3rd Speaker"  : entry.speaker_3_id,
            "3rd Topic"    : entry.topic_3
        }
    saved_hymns    = SelectedHymns.query.filter_by(meeting_center_id=meeting_center_id).all()

    # Obtén todos los himnos necesarios para combinar número y título
    hymn_ids = set()
    for entry in saved_hymns:
        hymn_ids.update([ 
            entry.opening_hymn_id,
            entry.sacrament_hymn_id,
            entry.intermediate_hymn_id,
            entry.closing_hymn_id
        ])


    # Consulta los himnos una sola vez
    hymn_map = {hymn.number: {'number': hymn.number, 'title': hymn.title} for hymn in Hymns.query.all()}
    used_hymns = get_hymn_usage(meeting_center_id)

    hymns_data = {}
    for entry in saved_hymns:
        date_str = entry.sunday_date.strftime('%Y-%m-%d')
        hymns_data[date_str] = {
            "Chorister"   : entry.music_director,
            "Accompanist"          : entry.pianist,
            "Opening Hymn"     : entry.opening_hymn_id,
            "Sacrament Hymn"   : entry.sacrament_hymn_id,
            "Intermediate Hymn": entry.intermediate_hymn_id,
            "Closing Hymn"     : entry.closing_hymn_id
        }

    
    return render_template('agendas/test.html', 
        youth_members=youth_members_serializable, 
        adult_members=adult_members_serializable,
        speakers_data=speakers_data,
        sundays_data=sundays_data, 
        hymns_data=hymns_data, 
        hymn_map=hymn_map,
        used_hymns=used_hymns,
        role=role)
