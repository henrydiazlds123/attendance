# app/routes/agenda.py
from datetime import datetime
from flask       import Blueprint, flash, render_template, redirect, request, url_for
from app.forms.hymn_form import HymnForm
from app.models  import db, Agenda, Bishopric, Member, SelectedHymns, WardAnnouncements, Speaker, WardBusiness
from app.forms   import AgendaForm
from flask_babel import gettext as _

from app.models.hymns_model import Hymns


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
    meeting_center_id = 1
    form = AgendaForm()

    # Llenar opciones de dropdown desde la base de datos
    form.director_id.choices = [(b.id, b.member.preferred_name) for b in Bishopric.query.all()]
    form.presider_id.choices = [(b.id, b.member.preferred_name) for b in Bishopric.query.all()]

    if request.method == 'GET' and request.args.get('sunday_date'):
        sunday_date = request.args.get('sunday_date')

        # Convertir string a datetime.date
        try:
            sunday_date = datetime.strptime(sunday_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de fecha inválido', 'danger')
            return redirect(url_for('new_agenda'))

        form.sunday_date.data = sunday_date  

        # Intentar cargar una agenda existente
        agenda = Agenda.query.filter_by(sunday_date=sunday_date, meeting_center_id=meeting_center_id).first()
        if agenda:
            form.director_id.data = agenda.director_id
            form.presider_id.data = agenda.presider_id
            form.opening_prayer.data = agenda.opening_prayer
            form.closing_prayer.data = agenda.closing_prayer

        # selected_hymns = SelectedHymns.query.filter_by(sunday_date=sunday_date, meeting_center_id=meeting_center_id).first()
        # if selected_hymns:
        #     form.hymns.entries = []  # Limpiar entradas previas
        #     hymns_data = [
        #         (selected_hymns.opening_hymn_id, 'Opening'),
        #         (selected_hymns.sacrament_hymn_id, 'Sacrament'),
        #         (selected_hymns.intermediate_hymn_id, 'Intermediate'),
        #         (selected_hymns.closing_hymn_id, 'Closing')
        #     ]

        #     for hymn_id, hymn_type in hymns_data:
        #         if hymn_id:  # Solo agregar si hay un himno asignado
        #             hymn = Hymns.query.get(hymn_id)
        #             if hymn:
        #                 form.hymns.append_entry({'number': hymn.number, 'hymn_type': hymn_type})
        selected_hymns = SelectedHymns.query.filter_by(sunday_date=sunday_date, meeting_center_id=meeting_center_id).first()
        if selected_hymns:
            form.hymns.entries = []  # Limpiar entradas previas
            hymns_data = [
                (selected_hymns.opening_hymn_id, 'Opening'),
                (selected_hymns.sacrament_hymn_id, 'Sacrament'),
                (selected_hymns.intermediate_hymn_id, 'Intermediate'),
                (selected_hymns.closing_hymn_id, 'Closing')
            ]

            for hymn_id, hymn_type in hymns_data:
                if hymn_id:  # Solo agregar si hay un himno asignado
                    hymn = Hymns.query.get(hymn_id)
                    if hymn:
                        hymn_entry = {
                            'hymn_number': hymn.number if hymn.number else '',  # Cambiar 'number' por 'hymn_number'
                            'hymn_type': hymn_type
                        }
                        form.hymns.append_entry(hymn_entry)  # Asignar el diccionario con datos directamente
 

        print(form.hymns.data)


        # Cargar discursos (independiente de la agenda)
        speakers = Speaker.query.filter_by(sunday_date=sunday_date, meeting_center_id=meeting_center_id).all()
        if speakers:
            form.speakers.entries = []
            for speaker in speakers:
                form.speakers.append_entry({'name': speaker.name, 'topic': speaker.topic})

    if form.validate_on_submit():
        # Crear nueva agenda
        agenda = Agenda(
            sunday_date       = form.sunday_date.data,
            director_id       = form.director_id.data,
            presider_id       = form.presider_id.data,
            opening_prayer    = form.opening_prayer.data,
            closing_prayer    = form.closing_prayer.data,
            meeting_center_id = meeting_center_id
        )
        db.session.add(agenda)

        # Guardar himnos (solo si no existían)
        for hymn_form in form.hymns.data:
            existing_hymn = SelectedHymns.query.filter_by(
                sunday_date       = agenda.sunday_date,
                hymn_number       = hymn_form['number'],
                meeting_center_id = meeting_center_id
            ).first()
            if not existing_hymn:
                hymn = SelectedHymns(sunday_date=agenda.sunday_date, hymn_number=hymn_form['number'], hymn_type=hymn_form['hymn_type'], meeting_center_id=meeting_center_id)
                db.session.add(hymn)

        # Guardar anuncios
        for ann in form.announcements.data:
            existing_announcement = WardAnnouncements.query.filter_by(sunday_date=agenda.sunday_date, text=ann['announcement_text']).first()
            if not existing_announcement:
                announcement = WardAnnouncements(sunday_date=agenda.sunday_date, text=ann['announcement_text'])
                db.session.add(announcement)

        # Guardar discursos (solo si no existían)
        for spk in form.speakers.data:
            existing_speaker = Speaker.query.filter_by(
                sunday_date       = agenda.sunday_date,
                name              = spk['name'],
                meeting_center_id = meeting_center_id
            ).first()
            if not existing_speaker:
                speaker = Speaker(sunday_date=agenda.sunday_date, name=spk['name'], topic=spk['topic'], meeting_center_id=meeting_center_id)
                db.session.add(speaker)

        # Guardar negocios del barrio (solo si no existían)
        for biz in form.business.data:
            existing_business = WardBusiness.query.filter_by(
                sunday_date       = agenda.sunday_date,
                member_id         = biz['member_id'],
                meeting_center_id = meeting_center_id
            ).first()
            if not existing_business:
                business = WardBusiness(
                    sunday_date           = agenda.sunday_date,
                    type                  = biz['type'],
                    member_id             = biz['member_id'],
                    calling_name          = biz['calling_name'],
                    baby_name             = biz['baby_name'],
                    blessing_officiant_id = biz['blessing_officiant_id'],
                    meeting_center_id     = meeting_center_id
                )
                db.session.add(business)

        db.session.commit()
        flash('Agenda creada exitosamente', 'success')
        return redirect(url_for('index'))

    return render_template('agendas/form.html', form=form)

