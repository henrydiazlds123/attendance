# app/routes/announcements.py
from flask import Blueprint, render_template, request, redirect, url_for
from app.models import db, WardAnnouncements, Agenda

bp_announcements = Blueprint('announcements', __name__)

@bp_announcements.route('/')
def announcements():
    announcements = WardAnnouncements.query.all()
    return render_template('/announcements/list.html', announcements=announcements)

@bp_announcements.route('/add', methods=['GET', 'POST'])
def add_announcement():
    if request.method == 'POST':
        agenda_id = request.form['agenda_id']
        details = request.form['details']
        
        new_announcement = WardAnnouncements(agenda_id=agenda_id, details=details)
        db.session.add(new_announcement)
        db.session.commit()
        return redirect(url_for('announcements.announcements'))
    
    agendas = Agenda.query.all()
    return render_template('/announcements/add.html', agendas=agendas)
