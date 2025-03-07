from flask                   import Blueprint, jsonify, request, session
from flask_babel             import gettext as _
from models                  import db, Classes, Attendance, MeetingCenter, Setup, NameCorrections
from utils                   import *
from datetime                import datetime, timedelta


bp_register = Blueprint('register', __name__)

    
# =============================================================================================
@bp_register.route('/', methods=['POST'])
def registrar():
    usuario       = session.get('user_name')
    # 🔍 Depurar: Ver qué datos llegan al servidor
    #print("Datos recibidos en el servidor:", request.form.to_dict())
    try:
        class_code   = request.form.get('classCode')
        sunday_date  = get_next_sunday()
        sunday_code  = request.form.get('sundayCode')
        unit_number  = request.form.get('unitNumber')
        student_name = request.form.get('studentName') 
               
        # Limpiar el nombre recibido
        student_name     = ' '.join(student_name.strip().split()) # Elimina espacios antes y después
        student_name     = student_name.title() # Convertir a título (primera letra en mayúscula) 
        student_name     = remove_accents(student_name) # Elimina los acentos
        nombre, apellido = student_name.split(" ", 1) # Dividir el nombre y apellido, asumiendo que solo hay un nombre y un apellido        
        formatted_name   = f"{apellido}, {nombre}" # Formatear el nombre como "apellido, nombre"

        # Verificar si la clase es válida
        class_entry = Classes.query.filter_by(class_code=class_code).first()
        #print(f"Class Entry: {class_entry}") 
        if not class_entry:
            return jsonify({
                "success": False,
                "message": _('The selected class is not valid.'),
            }), 409

        # Verificar si el Meeting Center es válido
        meeting_center = MeetingCenter.query.filter_by(unit_number=unit_number).first()
        if not meeting_center:
            return jsonify({
                "success": False,
                "message": _('The church unit is invalid.'),
            }), 409
        
        correction = NameCorrections.query.filter_by(wrong_name=formatted_name, meeting_center_id=meeting_center.id).first()
        if correction:
            formatted_name = correction.correct_name

        # Obtener el estado del bypass desde la tabla Setup
        bypass_entry  = Setup.query.filter_by(key='allow_weekday_attendance').first()
        bypass_active = bypass_entry and bypass_entry.value.lower() == 'yes'

        # Si la clase es Main y hay restricciones de día
        if class_entry.class_type == "Main":
            # Si el bypass NO está activo o la unidad NO es la de prueba (ID = 2), aplicar restricciones
            if not (bypass_active and meeting_center.id == 2):
                if meeting_center.is_restricted:
                    grace_period_hours = int(meeting_center.grace_period_hours) if meeting_center.grace_period_hours else 0
                    time_now           = datetime.now()

                    start_time = meeting_center.start_time
                    end_time   = meeting_center.end_time

                    if isinstance(start_time, str):
                        start_time = datetime.strptime(start_time, "%H:%M").time()
                    if isinstance(end_time, str):
                        end_time   = datetime.strptime(end_time, "%H:%M").time()

                    today            = datetime.today()
                    start_time_dt    = datetime.combine(today, start_time)
                    end_time_dt      = datetime.combine(today, end_time)
                    grace_start_time = start_time_dt - timedelta(hours=grace_period_hours)
                    grace_end_time   = end_time_dt + timedelta(hours=grace_period_hours)

                    if not (grace_start_time <= time_now <= grace_end_time):
                        return jsonify({
                            "success": False,
                            "message": _('Attendance can only be recorded during the grace period or meeting time.'),
                        }), 403

                # Verificar si ya existe un registro en una clase `Main` ese domingo
                existing_main_attendance = Attendance.query.filter_by(
                    student_name      = formatted_name,
                    sunday_date       = sunday_date,
                    meeting_center_id = meeting_center.id,
                ).join(Classes).filter(Classes.class_type == "Main").first()

                if existing_main_attendance:
                    return jsonify({
                        "success": False,
                        "error_type": "main_class_restriction",
                        "message": _("%(name)s! You have already registered for a Sunday class today!") % {'name': formatted_name}
                    }), 409

        elif class_entry.class_type == "Extra":
            # Verificar si ya existe un registro para una clase `Extra` ese domingo
            existing_extra_attendance = Attendance.query.filter_by(
                student_name      = formatted_name,
                class_id          = class_entry.id,
                sunday_date       = sunday_date,
                meeting_center_id = meeting_center.id
            ).first()

            if existing_extra_attendance:
                return jsonify({
                    "success": False,
                    "message": _("%(name)s! You already have an attendance registered for this class on Sunday %(date)s!") % {
                        'name': formatted_name, 
                        'date': sunday_date.strftime('%b %d, %Y')
                    }
                }), 400
            
        created_by = nombre # Usa el nombre del estudiante para este campo
        if usuario:
            created_by = usuario # Si el usuario esta autenticado, se usa su nombre
        
        # Registrar la asistencia
        new_attendance = Attendance(
            student_name        = formatted_name,
            class_id            = class_entry.id,
            class_code          = class_code,
            sunday_date         = sunday_date,
            sunday_code         = sunday_code,
            meeting_center_id   = meeting_center.id,
            created_by          = created_by
        )
        db.session.add(new_attendance)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": _('Attendance recorded successfully.'),
            "student_name": student_name,
            "class_name": class_entry.class_name,
            "sunday_date": sunday_date.strftime("%b %d, %Y")
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": _('There was an error recording attendance: %(error)s') % {'error': str(e)}
        }), 500