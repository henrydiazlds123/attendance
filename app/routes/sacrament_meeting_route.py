# app/routes/sacrament_meeting.py
from flask import Blueprint, render_template, redirect, url_for
from app.models import db, SacramentMeeting
from app.forms import SacramentMeetingForm

# Creamos el Blueprint
bp_sacrament_meeting = Blueprint('sacramental', __name__)

@bp_sacrament_meeting.route('/')
def sacrament_meetings():
    meetings = SacramentMeeting.query.all()
    return render_template('/sacrament_meetings/list.html', meetings=meetings)


@bp_sacrament_meeting.route('/add', methods=['GET', 'POST'])
def add_sacrament_meeting():
    form = SacramentMeetingForm()
    if form.validate_on_submit():
        new_meeting = SacramentMeeting(
            sunday_date=form.sunday_date.data,
            director_id=form.director_id.data
        )
        db.session.add(new_meeting)
        db.session.commit()
        return redirect(url_for('sacrament_meeting_bp.sacrament_meetings'))
    return render_template('/sacrament_meetings/add.html', form=form)
