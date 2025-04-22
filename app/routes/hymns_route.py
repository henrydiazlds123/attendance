# app/routes/hymns.py
from flask      import Blueprint, jsonify, render_template, request, redirect, url_for
from app.models import db, Hymns, SelectedHymns, Speaker
from datetime   import datetime, timedelta
from app.utils  import *
from flask_babel    import gettext as _


bp_hymns = Blueprint('hymns', __name__)


# =============================================================================================
@bp_hymns.route('/')
def hymns():
    hymns = Hymns.query.all()
    # Agrupar himnos por tema
    hymns_by_topic = {}
    for hymn in hymns:
        topic_name = hymn.get_topic_name()
        if topic_name not in hymns_by_topic:
            hymns_by_topic[topic_name] = []
        hymns_by_topic[topic_name].append(hymn)
    
    return render_template('/hymns/list.html', hymns_by_topic=hymns_by_topic)


# =============================================================================================
@bp_hymns.route('/add', methods=['GET', 'POST'])
def add_hymn():
    if request.method == 'POST':
        number = request.form['number']
        title = request.form['title']
        
        new_hymn = Hymns(number=number, title=title)
        db.session.add(new_hymn)
        db.session.commit()
        return redirect(url_for('hymns.hymns'))
    
    return render_template('/hymns/add.html')


# =============================================================================================
@bp_hymns.route('/agenda', methods=['GET', 'POST'])
def agenda():
    meeting_center_id = 1  # Temporalmente fijo

    if request.method == 'POST':
        data = request.json  # Datos desde la tabla
        #print(f'Data: {data}')
        date_map = {}  # Reorganizar los datos por fecha

        # Agrupar datos por fecha
        for row in data:
            hymn_name = row['hymn_name']
            for date, value in row.items():
                if date == 'hymn_name':
                    continue
                if date not in date_map:
                    date_map[date] = {}
                date_map[date][hymn_name] = value

        # Funciones auxiliares para asignar valores solo si hay dato válido
        def assign_if_present(obj, attr, value):
            if value not in [None, '']:
                setattr(obj, attr, value)

        def assign_if_present_int(obj, attr, value):
            try:
                int_value = int(value)
                setattr(obj, attr, int_value)
            except (ValueError, TypeError):
                pass  # No asignar si no es número válido

        # Primero, eliminamos las entradas existentes para el Meeting Center y las fechas
        for date_str in date_map.keys():
            sunday_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Eliminar las entradas de la base de datos para las fechas y el Meeting Center
            SelectedHymns.query.filter_by(
                sunday_date=sunday_date,
                meeting_center_id=meeting_center_id
            ).delete()

        # Procesar y guardar los nuevos datos
        for date_str, hymns in date_map.items():
            sunday_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Crear nueva entrada si no existe
            hymn_entry = SelectedHymns(
                sunday_date=sunday_date,
                meeting_center_id=meeting_center_id
            )
            db.session.add(hymn_entry)

            # Asignaciones seguras para cada himno
            assign_if_present(hymn_entry, 'music_director', hymns.get('Chorister'))
            assign_if_present(hymn_entry, 'pianist', hymns.get("Accompanist"))
            assign_if_present_int(hymn_entry, 'opening_hymn_id', hymns.get("Opening Hymn"))
            assign_if_present_int(hymn_entry, 'sacrament_hymn_id', hymns.get("Sacrament Hymn"))
            assign_if_present_int(hymn_entry, 'intermediate_hymn_id', hymns.get("Intermediate Hymn"))
            assign_if_present_int(hymn_entry, 'closing_hymn_id', hymns.get("Closing Hymn"))

        db.session.commit()

        return jsonify({'message': 'Datos guardados correctamente'}), 200

    # GET
    today        = datetime.today()
    start_date   = datetime(today.year, (today.month - 1) // 3 * 3 + 1, 1)
    #start_date   = datetime(2025, 1, 1)
    end_date     = start_date + timedelta(days=90)
    sundays_data = get_sundays(start_date, end_date)

    saved_hymns    = SelectedHymns.query.filter_by(meeting_center_id=meeting_center_id).all()
    saved_speakers = Speaker.query.filter_by(meeting_center_id=meeting_center_id).all()

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
    hymns    = Hymns.query.filter(Hymns.number.in_(hymn_ids)).all()
    hymn_map = {hymn.number: {'number': hymn.number, 'title': hymn.title} for hymn in Hymns.query.all()}

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

    speakers_data = {}
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

    return render_template("hymns/agenda.html", sundays_data=sundays_data, hymns_data=hymns_data, hymn_map=hymn_map, speakers_data=speakers_data)