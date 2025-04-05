# app/routes/speakers.py
from flask import Blueprint, render_template, request, redirect, url_for
from app.forms import SpeakerForm
from app.models import db, Speaker, Member


bp_speakers = Blueprint('speakers', __name__)


# =============================================================================================
@bp_speakers.route('/')
def speakers():
    speakers = Speaker.query.all()
    return render_template('/speakers/list.html', speakers=speakers)


# =============================================================================================
@bp_speakers.route('/agenda')
def agenda():
    # Suponiendo que "Agenda" tiene la relación con "Speaker" y tiene los datos de fechas y temas
    agenda_data = db.session.query(Speaker.sunday_date, Speaker.member_id, Speaker.topic, Member.full_name, Speaker.meeting_center_id).join(Member).all()

    # Formateamos los datos en un formato adecuado para Handsontable
    formatted_data = {}
    
    for entry in agenda_data:
        sunday_date = entry.sunday_date.strftime('%d %b')  # Formato para las fechas
        if sunday_date not in formatted_data:
            formatted_data[sunday_date] = {}
        
        # Asociamos la información por domingo y miembro
        formatted_data[sunday_date][entry.member_id] = {'topic': entry.topic, 'member_name': entry.name}
    
    return render_template('speakers/agenda.html', agenda=formatted_data)


# =============================================================================================
@bp_speakers.route('/add', methods=['GET', 'POST'])
def add_speaker():
    form = SpeakerForm()
    if form.validate_on_submit():  # Usamos validate_on_submit() para comprobar si el formulario es válido
        new_speaker = Speaker(
            agenda_id=form.agenda_id.data,
            name=form.name.data,
            topic=form.topic.data
        )
        db.session.add(new_speaker)
        db.session.commit()
        return redirect(url_for('speakers.speakers'))  # Redirigir a la lista de oradores
    
    return render_template('speakers/add.html', form=form)
