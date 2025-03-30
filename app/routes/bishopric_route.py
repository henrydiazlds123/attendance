from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db, Member, Bishopric, MeetingCenter
from sqlalchemy.orm.exc import NoResultFound

bp_bishopric = Blueprint('bishopric', __name__)

@bp_bishopric.route('/manage/<int:meeting_center_id>', methods=['GET', 'POST'])
def manage_bishopric(meeting_center_id):
    # Llamamientos permitidos
    allowed_roles = ["Bishop", "Bishopric First Counselor", "Bishopric Second Counselor"]

    # Obtener miembros con estos llamamientos en el centro de reunión
    members = Member.query.filter(
        Member.calling.in_(allowed_roles),
        Member.meeting_center_id == meeting_center_id
    ).all()

    # Obtener datos actuales del obispado
    current_bishopric = {b.role: b.member_id for b in Bishopric.query.filter_by(meeting_center_id=meeting_center_id).all()}

    if request.method == 'POST':
        try:
            for role in allowed_roles:
                member_id = request.form.get(role)

                if member_id:
                    member_id = int(member_id)

                    # Verificar si ya existe ese rol y actualizarlo
                    bishopric_entry = Bishopric.query.filter_by(meeting_center_id=meeting_center_id, role=role).first()
                    if bishopric_entry:
                        bishopric_entry.member_id = member_id
                    else:
                        new_entry = Bishopric(
                            member_id=member_id,
                            role=role,
                            meeting_center_id=meeting_center_id
                        )
                        db.session.add(new_entry)

            db.session.commit()
            flash('Obispado actualizado correctamente', 'success')
            return redirect(url_for('bishopric.manage_bishopric', meeting_center_id=meeting_center_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el obispado: {str(e)}', 'danger')

    return render_template('bishopric/manage.html', members=members, current_bishopric=current_bishopric, meeting_center_id=meeting_center_id, roles=allowed_roles)
