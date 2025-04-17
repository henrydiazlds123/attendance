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
# @bp_hymns.route('/agenda', methods=['GET', 'POST'])
# def agenda():
#     meeting_center_id = 1  # Temporalmente fijo

#     if request.method == 'POST':
#         data = request.json  # Datos desde la tabla
#         date_map = {}  # Reorganizar los datos por fecha

#         # Agrupar datos por fecha
#         for row in data:
#             hymn_name = row['hymn_name']
#             for date, value in row.items():
#                 if date == 'hymn_name':
#                     continue
#                 if date not in date_map:
#                     date_map[date] = {}
#                 date_map[date][hymn_name] = value

#         # Funciones auxiliares para asignar valores solo si hay dato válido
#         def assign_if_present(obj, attr, value):
#             if value not in [None, '']:
#                 setattr(obj, attr, value)

#         def assign_if_present_int(obj, attr, value):
#             try:
#                 int_value = int(value)
#                 setattr(obj, attr, int_value)
#             except (ValueError, TypeError):
#                 pass  # No asignar si no es número válido

#         # Procesar cada fecha
#         for date_str, hymns in date_map.items():
#             sunday_date = datetime.strptime(date_str, '%Y-%m-%d').date()

#             hymn_entry = SelectedHymns.query.filter_by(
#                 sunday_date=sunday_date,
#                 meeting_center_id=meeting_center_id
#             ).first()

#             if not hymn_entry:
#                 hymn_entry = SelectedHymns(
#                     sunday_date=sunday_date,
#                     meeting_center_id=meeting_center_id
#                 )
#                 db.session.add(hymn_entry)

#             # Asignaciones seguras
#             assign_if_present(hymn_entry, 'music_director', hymns.get("Director"))
#             assign_if_present(hymn_entry, 'pianist', hymns.get("Pianista"))
#             assign_if_present_int(hymn_entry, 'opening_hymn_id', hymns.get("Primer Himno"))
#             assign_if_present_int(hymn_entry, 'sacrament_hymn_id', hymns.get("Himno Sacramental"))
#             assign_if_present_int(hymn_entry, 'intermediate_hymn_id', hymns.get("Himno Intermedio"))
#             assign_if_present_int(hymn_entry, 'closing_hymn_id', hymns.get("Ultimo Himno"))

#         db.session.commit()

#         return jsonify({'message': 'Datos guardados correctamente'}), 200


#     # GET
#     today       = datetime.today()
#     start_date  = datetime(today.year, (today.month - 1) // 3 * 3 + 1, 1)
#     end_date    = start_date + timedelta(days=90)
#     sundays     = get_sundays(start_date, end_date)

#     saved_hymns = SelectedHymns.query.filter_by(meeting_center_id=meeting_center_id).all()

#     # Obtén todos los himnos necesarios para combinar número y título
#     hymn_ids = set()
#     for entry in saved_hymns:
#         hymn_ids.update([
#             entry.opening_hymn_id,
#             entry.sacrament_hymn_id,
#             entry.intermediate_hymn_id,
#             entry.closing_hymn_id
#         ])

#     # Consulta los himnos una sola vez
#     hymns = Hymns.query.filter(Hymns.number.in_(hymn_ids)).all()
#     # Este es el map que envías adicionalmente al render
#     hymn_map = {hymn.id: {'number': hymn.number, 'title': hymn.title} for hymn in Hymns.query.all()}

#     # print(f"Himnos encontrados: {hymn_map}")

#     # Los datos para la tabla siguen usando IDs (esto es importante para guardar bien)
#     hymns_data = {}
#     for entry in saved_hymns:
#         date_str = entry.sunday_date.strftime('%Y-%m-%d')
#         hymns_data[date_str] = {
#             "Director": entry.music_director,
#             "Pianista": entry.pianist,
#             "Primer Himno": entry.opening_hymn_id,
#             "Himno Sacramental": entry.sacrament_hymn_id,
#             "Himno Intermedio": entry.intermediate_hymn_id,
#             "Ultimo Himno": entry.closing_hymn_id
#         }
#     print(f"Datos de himnos: {hymns_data}") 

#     return render_template("hymns/selected.html", sundays=sundays, hymns_data=hymns_data, hymn_map=hymn_map)


@bp_hymns.route('/agenda', methods=['GET', 'POST'])
def agenda():
    meeting_center_id = 1  # Temporalmente fijo

    if request.method == 'POST':
        data = request.json  # Datos desde la tabla
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
            assign_if_present(hymn_entry, 'music_director', hymns.get("Director"))
            assign_if_present(hymn_entry, 'pianist', hymns.get("Pianista"))
            assign_if_present_int(hymn_entry, 'opening_hymn_id', hymns.get("Primer Himno"))
            assign_if_present_int(hymn_entry, 'sacrament_hymn_id', hymns.get("Himno Sacramental"))
            assign_if_present_int(hymn_entry, 'intermediate_hymn_id', hymns.get("Himno Intermedio"))
            assign_if_present_int(hymn_entry, 'closing_hymn_id', hymns.get("Ultimo Himno"))

        db.session.commit()

        return jsonify({'message': 'Datos guardados correctamente'}), 200

    # GET
    today        = datetime.today()
    start_date   = datetime(today.year, (today.month - 1) // 3 * 3 + 1, 1)
    end_date     = start_date + timedelta(days=90)
    sundays_data = get_sundays(start_date, end_date)

    saved_hymns = SelectedHymns.query.filter_by(meeting_center_id=meeting_center_id).all()

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
    hymns = Hymns.query.filter(Hymns.number.in_(hymn_ids)).all()

    # Este es el map que envías adicionalmente al render
    hymn_map = {hymn.number: {'number': hymn.number, 'title': hymn.title} for hymn in Hymns.query.all()}

    # Los datos para la tabla siguen usando IDs (esto es importante para guardar bien)
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

    return render_template("hymns/selected.html", sundays_data=sundays_data, hymns_data=hymns_data, hymn_map=hymn_map)
