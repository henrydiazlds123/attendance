# app/routes/hymns.py
from flask      import Blueprint, jsonify, render_template, request, redirect, url_for
from app.models import db, Hymns, SelectedHymns
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
def hymns_agenda():
    meeting_center_id = 1  # Temporalmente fijo

    if request.method == 'POST':
        data = request.json  # Datos desde la tabla

        # Reorganizar los datos por fecha
        date_map = {}

        for row in data:
            hymn_name = row['hymn_name']
            for date, value in row.items():
                if date == 'hymn_name':
                    continue
                if date not in date_map:
                    date_map[date] = {}
                date_map[date][hymn_name] = value

        for date_str, hymns in date_map.items():
            #print(f"Procesando fecha: {date_str}")
            sunday_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            hymn_entry = SelectedHymns.query.filter_by(
                sunday_date=sunday_date,
                meeting_center_id=meeting_center_id
            ).first()

            if hymn_entry:
                print(f"Actualizando registro existente para {sunday_date}")
            else:
                hymn_entry = SelectedHymns(
                    sunday_date=sunday_date,
                    meeting_center_id=meeting_center_id
                )
                db.session.add(hymn_entry)
                print(f"Creando nuevo registro para {sunday_date}")

            # Asignar los valores (convertir a int si aplica)
            hymn_entry.music_director = hymns.get("Director")
            hymn_entry.pianist = hymns.get("Pianista")

            def to_int(val):
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return None

            hymn_entry.opening_hymn_id = to_int(hymns.get("Primer Himno"))
            hymn_entry.sacrament_hymn_id = to_int(hymns.get("Himno Sacramental"))
            hymn_entry.intermediate_hymn_id = to_int(hymns.get("Himno Intermedio"))
            hymn_entry.closing_hymn_id = to_int(hymns.get("Ultimo Himno"))

        db.session.commit()
        #print("Cambios guardados correctamente.")
        return jsonify({"message": _('Data saved successfully')}), 200

    # GET
    today = datetime.today()
    start_date = datetime(today.year, (today.month - 1) // 3 * 3 + 1, 1)
    end_date = start_date + timedelta(days=90)
    sundays = get_sundays(start_date, end_date)

    saved_hymns = SelectedHymns.query.all()

    hymns_data = {}
    for entry in saved_hymns:
        date_str = entry.sunday_date.strftime('%Y-%m-%d')
        hymns_data[date_str] = {
            "Director": entry.music_director,
            "Pianista": entry.pianist,
            "Primer Himno": entry.opening_hymn_id,
            "Himno Sacramental": entry.sacrament_hymn_id,
            "Himno Intermedio": entry.intermediate_hymn_id,
            "Ultimo Himno": entry.closing_hymn_id
        }

    return render_template("hymns/selected.html", sundays=sundays, hymns_data=hymns_data)
