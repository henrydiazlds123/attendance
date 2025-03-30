# app/routes/hymns.py
from flask      import Blueprint, jsonify, render_template, request, redirect, url_for
from app.models import db, Hymns, SelectedHymns
from datetime   import datetime, timedelta
from sqlalchemy import func
from app.utils  import *


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



def get_sundays(start_date, end_date):
    """Genera una lista de domingos entre dos fechas."""
    # Ajusta la fecha de inicio al próximo domingo si no es domingo
    current = start_date
    if current.weekday() != 6:  # Si no es domingo
        days_to_add = 6 - current.weekday()  # Días hasta el siguiente domingo
        current += timedelta(days=days_to_add)
    
    sundays = []
    while current <= end_date:
        sundays.append(current.strftime('%Y-%m-%d'))
        current += timedelta(weeks=1)  # Avanzar una semana

    return sundays


# =============================================================================================
@bp_hymns.route('/agenda', methods=['GET', 'POST'])
def hymns_agenda():
    meeting_center_id = 1  # Temporalmente fijo
    if request.method == 'POST':
        data = request.json  # Datos desde la tabla
        print(data)

        for date in data[0].keys():
            if date == "hymn_name":
                continue
            
            sunday_date = datetime.strptime(date, '%Y-%m-%d')
            # sunday_date = sunday_date.date()  # Esto elimina la hora

            # Buscar el registro existente basado en sunday_date y meeting_center_id
            # hymn_entry = SelectedHymns.query.filter_by(sunday_date=sunday_date, meeting_center_id=meeting_center_id).first()
            hymn_entry = SelectedHymns.query.filter(
                func.date(SelectedHymns.sunday_date) == sunday_date.date(),
                SelectedHymns.meeting_center_id == meeting_center_id
            ).first()

            # Si no existe el registro, no creamos uno nuevo, solo actualizamos
            if hymn_entry:
                print(f"Registro encontrado para {sunday_date} y meeting_center_id {meeting_center_id}")
                
                # Actualizar los valores correspondientes
                for row in data:
                    value = row[date]
                    if row["hymn_name"] == "Director":
                        hymn_entry.music_director = value
                    elif row["hymn_name"] == "Pianista":
                        hymn_entry.pianist = value
                    elif row["hymn_name"] == "Primer Himno":
                        hymn_entry.opening_hymn_id = value
                    elif row["hymn_name"] == "Himno Sacramental":
                        hymn_entry.sacrament_hymn_id = value
                    elif row["hymn_name"] == "Himno Intermedio":
                        hymn_entry.intermediate_hymn_id = value
                    elif row["hymn_name"] == "Ultimo Himno":
                        hymn_entry.closing_hymn_id = value
                
                # Imprimir para asegurarse de que estamos actualizando el registro
                print(f"Actualizando registro para {sunday_date}")
            else:
                print(f"No se encontró el registro para {sunday_date}, no se actualizará.")
                return jsonify({"error": "No se encontró el registro para esta fecha."}), 400

        # Guardar los cambios en la base de datos
        db.session.commit()
        print("Cambios guardados correctamente.")
        return jsonify({"message": "Datos guardados exitosamente"}), 200

    # Generar los domingos del trimestre actual
    today = datetime.today()
    start_date = datetime(today.year, (today.month - 1) // 3 * 3 + 1, 1)
    end_date = start_date + timedelta(days=90)
    sundays = get_sundays(start_date, end_date)

    # Obtener datos guardados en la BD
    saved_hymns = SelectedHymns.query.all()

    # Convertir datos en un diccionario JSON
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
