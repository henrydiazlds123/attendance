# app/routes/agenda.py
from flask       import Blueprint, flash, jsonify, render_template, redirect, request, url_for
from app.forms import HymnForm, AgendaForm
from app.models  import db, Agenda, Bishopric, Member, SelectedHymns, WardAnnouncements, Speaker, WardBusiness, Hymns, MeetingCenter

from flask_babel import gettext as _


bp_agenda = Blueprint('agenda', __name__)


# =============================================================================================
@bp_agenda.route('/')
def list_agendas():
    meetings = Agenda.query.order_by(Agenda.sunday_date.desc()).all()
    return render_template('/agendas/list.html', meetings=meetings)


# =============================================================================================
@bp_agenda.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_agenda(id):
    meeting = Agenda.query.get_or_404(id)
    form = AgendaForm(obj=meeting)
    if form.validate_on_submit():
        meeting.sunday_date       = form.sunday_date.data
        meeting.director_id       = form.director_id.data
        meeting.presider_id       = form.presider_id.data
        meeting.closing_prayer    = form.closing_prayer.data
        meeting.meeting_center_id = form.meeting_center_id.data
        db.session.commit()
        flash(_('Sacrament Meeting Agenda Updated'), "success")
        return redirect(url_for('agenda.list_agendas'))
    return render_template('agendas/form.html', form=form)


# =============================================================================================
@bp_agenda.route('/delete/<int:id>', methods=['POST'])
def delete_agenda(id):
    meeting = Agenda.query.get_or_404(id)
    db.session.delete(meeting)
    db.session.commit()
    flash("Agenda deleted", "danger")
    return redirect(url_for('agenda.list_agendas'))


# =============================================================================================
@bp_agenda.route('/new', methods=['GET', 'POST'])
def new_agenda():
    form = AgendaForm()

    # Poblar choices de la base de datos
    form.director_id.choices          = [(b.id, b.member.preferred_name) for b in Bishopric.query.all()]
    form.presider_id.choices          = [(b.id, b.member.preferred_name) for b in Bishopric.query.all()]
    form.meeting_center_id.choices    = [(m.id, m.name) for m in MeetingCenter.query.all()]
    hymns                             = Hymns.query.all()
    hymn_choices                      = [(h.number, h.title) for h in hymns]
    form.opening_hymn_id.choices      = hymn_choices
    form.sacrament_hymn_id.choices    = hymn_choices
    form.intermediate_hymn_id.choices = hymn_choices
    form.closing_hymn_id.choices      = hymn_choices

    if form.validate_on_submit():
        # Crear agenda
        agenda = Agenda(
            sunday_date          = form.sunday_date.data,
            meeting_center_id    = form.meeting_center_id.data,
            director_id          = form.director_id.data,
            presider_id          = form.presider_id.data,
            opening_prayer       = form.opening_prayer.data,
            closing_prayer       = form.closing_prayer.data,
            opening_hymn_id      = form.opening_hymn_id.data,
            sacrament_hymn_id    = form.sacrament_hymn_id.data,
            intermediate_hymn_id = form.intermediate_hymn_id.data,
            closing_hymn_id      = form.closing_hymn_id.data
        )
        db.session.add(agenda)

        # Oradores
        for speaker_form in form.speakers:
            if speaker_form.speaker_name.data:  # Accede al campo específico
                speaker = Speaker(name=speaker_form.speaker_name.data, agenda=agenda)
                db.session.add(speaker)

        # Anuncios
        for announcement_form in form.announcements:  # Itera sobre los formularios
            if announcement_form.announcement_text.data:  # Accede al campo específico
                announcement = WardAnnouncements(
                    text=announcement_form.announcement_text.data,
                    agenda=agenda
                )
                db.session.add(announcement)

        # Asuntos de barrio
        for business_form in form.business:  # Itera sobre los formularios
            if business_form.text.data:  # Accede al campo específico
                business = WardBusiness(text=business_form.text.data, agenda=agenda)
                db.session.add(business)

        db.session.commit()
        flash('Agenda created successfully!', 'success')
        return redirect(url_for('bp_agenda.new_agenda'))

    return render_template('agendas/new_agenda.html', form=form)