# app/routes/speakers.py
from datetime import datetime
from flask import Blueprint, jsonify, render_template, request, redirect, url_for
from app.forms import SpeakerForm
from app.models import db, Speaker, Member
from app.models.meeting_centers_model import MeetingCenter
from app.utils      import *
from flask_babel  import gettext as _


bp_speakers = Blueprint('speakers', __name__)


# =============================================================================================
@bp_speakers.route('/')
def speakers():
    speakers = Speaker.query.all()
    return render_template('/speakers/list.html', speakers=speakers)


# =============================================================================================
@bp_speakers.route('/add', methods=['GET', 'POST'])
def add_speaker():
    meeting_center_id = 1
    meeting_centers = MeetingCenter.query.all()

    today = datetime.today()

    active_members = Member.query.filter(
        Member.active == True,
        Member.meeting_center_id == meeting_center_id,
        Member.birth_date.isnot(None)
    ).order_by(Member.preferred_name)

    youth_cutoff = datetime(today.year - 11, today.month, today.day)
    senior_cutoff = datetime(today.year - 17, today.month, today.day)

    youth_members = active_members.filter(
        Member.birth_date.between(senior_cutoff, youth_cutoff)
    ).all()

    adult_members = active_members.filter(
        Member.birth_date < senior_cutoff
    ).all()

    form = SpeakerForm()
    form.youth_speaker_id.choices = [(m.id, m.preferred_name) for m in youth_members]
    form.speaker_1_id.choices = [(m.id, m.preferred_name) for m in adult_members]
    form.speaker_2_id.choices = [(m.id, m.preferred_name) for m in adult_members]
    form.speaker_3_id.choices = [(m.id, m.preferred_name) for m in adult_members]
    form.meeting_center_id.choices = [(c.id, c.short_name) for c in meeting_centers]

    if form.validate_on_submit():
        new_speaker = Speaker(
            sunday_date=form.sunday_date.data,
            youth_speaker_id=form.youth_speaker_id.data,
            youth_topic=form.youth_topic.data,
            speaker_1_id=form.speaker_1_id.data,
            topic_1=form.topic_1.data,
            speaker_2_id=form.speaker_2_id.data,
            topic_2=form.topic_2.data,
            speaker_3_id=form.speaker_3_id.data,
            topic_3=form.topic_3.data,
            meeting_center_id=form.meeting_center_id.data
        )

        db.session.add(new_speaker)
        db.session.commit()

        flash('Speaker added successfully!', 'success')
        return redirect(url_for('speakers.speakers_agenda'))  # Redirige a la tabla Excel

    return render_template('speakers/add.html', form=form)


# =============================================================================================
@bp_speakers.route('/agenda', methods=['GET', 'POST'])
def speakers_agenda():
    meeting_center_id = 1  # Asegúrate de asignar el ID del centro de reunión adecuado

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

    if request.method == 'POST':
        data = request.json

        if not data:
            return jsonify({'status': 'error', 'message': 'No data received from frontend'}), 400

        # Orden esperado de campos desde el frontend
        fields = [
            'Youth Speaker',
            'Youth Topic',
            '1st Speaker',
            '1st Topic',
            '2nd Speaker',
            '2nd Topic',
            '3rd Speaker',
            '3rd Topic'
        ]

        date_map = {}

        for idx, row in enumerate(data):
            for date, value in row.items():
                if date not in date_map:
                    date_map[date] = {}
                # Usamos idx para mapear el campo correcto
                field_name = fields[idx]

                if 'Speaker' in field_name and str(value).isdigit():
                    member = Member.query.filter_by(id=int(value)).first()
                    if member:
                        value = member.preferred_name

                date_map[date][field_name] = value
        
        # Procesar los datos de entrada
        for row in data:
            for date, roles in row.items():
                # Comprobar que roles sea un diccionario
                if isinstance(roles, dict):
                    if date not in date_map:
                        date_map[date] = {}

                    for field in fields:
                        value = roles.get(field, '')

                        # Si es un campo de Speaker y el valor es un ID, obtenemos el preferred_name
                        if 'Speaker' in field and str(value).isdigit():
                            member = Member.query.filter_by(id=int(value)).first()
                            if member:
                                value = member.preferred_name

                        if value:
                            date_map[date][field] = value

        # Guardar los datos en la base de datos
        for date_str, roles in date_map.items():
            try:
                sunday_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError as e:
                print(f"Error converting date {date_str}: {e}")
                continue

            # Buscar o crear una entrada en la base de datos
            speaker_entry = Speaker.query.filter_by(
                sunday_date=sunday_date,
                meeting_center_id=meeting_center_id
            ).first()

            if not speaker_entry:
                speaker_entry = Speaker(
                    sunday_date=sunday_date,
                    meeting_center_id=meeting_center_id
                )
                db.session.add(speaker_entry)
                print(f"New speaker entry added for {sunday_date}")

            # Actualizar los roles del orador
            print(f"Saving speaker entry for {sunday_date}: {roles}")
            speaker_entry.youth_speaker_id = roles.get('Youth Speaker', None)
            speaker_entry.youth_topic      = roles.get('Youth Topic', None)
            speaker_entry.speaker_1_id     = roles.get('1st Speaker', None)
            speaker_entry.topic_1          = roles.get('1st Topic', None)
            speaker_entry.speaker_2_id     = roles.get('2nd Speaker', None)
            speaker_entry.topic_2          = roles.get('2nd Topic', None)
            speaker_entry.speaker_3_id     = roles.get('3rd Speaker', None)
            speaker_entry.topic_3          = roles.get('3rd Topic', None)

        try:
            db.session.commit()
            print("Database commit successful.")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing to the database: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

        return jsonify({'status': 'success', 'message': 'Data processed and saved successfully'})

    # GET
    today      = datetime.today()
    start_date = datetime(today.year, (today.month - 1) // 3 * 3 + 1, 1)
    end_date   = start_date + timedelta(days=90)
    sundays    = get_sundays(start_date, end_date)

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
    
    return render_template('speakers/agenda.html', 
        youth_members=youth_members_serializable, 
        adult_members=adult_members_serializable,
        sundays=sundays, 
        speakers_data=speakers_data)
