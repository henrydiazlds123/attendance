# app/routes/hymns.py
from flask      import Blueprint, jsonify, render_template, request, redirect, url_for
from app.models import db, Hymns, SelectedHymns
from datetime   import datetime, timedelta


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
    current = start_date
    sundays = []
    while current <= end_date:
        if current.weekday() == 6:  # Domingo
            sundays.append(current.strftime('%Y-%m-%d'))
            # sundays.append(current.strftime('%d %b'))
        current += timedelta(days=1)
    return sundays


# =============================================================================================
@bp_hymns.route('/agenda', methods=['GET', 'POST'])
def hymns_agenda():
    if request.method == 'POST':
        data = request.json  # Datos desde la tabla

        for date in data[0].keys():  # Iterar sobre las fechas (excepto "hymn_name")
            if date == "hymn_name":
                continue
            
            sunday_date = datetime.strptime(date, '%Y-%m-%d')

            # Buscar si ya existe un registro para este domingo
            hymn_entry = SelectedHymns.query.filter_by(sunday_date=sunday_date).first()

            if not hymn_entry:
                hymn_entry = SelectedHymns(sunday_date=sunday_date)
                db.session.add(hymn_entry)

            # Recorrer cada fila para asignar los valores correctos en su columna
            for row in data:
                value = row[date]  # Valor en la celda correspondiente a esta fecha
                
                if row["hymn_name"] == "Director":
                    hymn_entry.music_director = value
                elif row["hymn_name"] == "Pianista":
                    hymn_entry.pianist = value
                elif row["hymn_name"] == "Primer Himnos":
                    hymn_entry.opening_hymn_id = value
                elif row["hymn_name"] == "Himno Sacramental":
                    hymn_entry.sacrament_hymn_id = value
                elif row["hymn_name"] == "Himno Intermedio":
                    hymn_entry.intermediate_hymn_id = value
                elif row["hymn_name"] == "Ultimo Himno":
                    hymn_entry.closing_hymn_id = value

        db.session.commit()
        return jsonify({"message": "Datos guardados exitosamente"}), 200

    # Generar los domingos del trimestre actual
    today      = datetime.today()
    start_date = datetime(today.year, (today.month - 1) // 3 * 3 + 1, 1)
    end_date   = start_date + timedelta(days=90)
    sundays    = get_sundays(start_date, end_date)

    return render_template("hymns/selected.html", sundays=sundays)

