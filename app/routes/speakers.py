# app/routes/speakers.py
from flask import Blueprint, render_template, request, redirect, url_for
from app.models import db, Speakers, SacramentAgenda

bp_speakers = Blueprint('speakers', __name__)

@bp_speakers.route('/')
def speakers():
    speakers = Speakers.query.all()
    return render_template('/speakers/list.html', speakers=speakers)

@bp_speakers.route('/add', methods=['GET', 'POST'])
def add_speaker():
    if request.method == 'POST':
        agenda_id = request.form['agenda_id']
        name = request.form['name']
        topic = request.form['topic']
        
        new_speaker = Speakers(agenda_id=agenda_id, name=name, topic=topic)
        db.session.add(new_speaker)
        db.session.commit()
        return redirect(url_for('speakers.speakers'))
    
    agendas = SacramentAgenda.query.all()
    return render_template('/speakers/add.html', agendas=agendas)
