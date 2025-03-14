import qrcode
from flask                   import Blueprint, abort, render_template, redirect, request, session, url_for, flash, send_from_directory
from flask_babel             import gettext as _
from app.config              import Config
from app.models              import Classes
from app.utils               import *
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils     import ImageReader
from reportlab.pdfgen        import canvas
from urllib.parse            import unquote
from datetime                import datetime

bp_pdf = Blueprint('pdf', __name__)

@bp_pdf.route('/list', methods=['GET'])
@login_required
def list_pdfs():
    meeting_center_id = get_meeting_center_id()
    OUTPUT_DIR = get_output_dir()
    
    # Verificar si hay clases asociadas al meeting center
    has_classes       = Classes.query.filter_by(meeting_center_id=meeting_center_id, is_active=True).first() is not None
    
    # Verificar si hay clases 'Main' o 'Extra' activas
    has_main_classes  = Classes.query.filter_by(meeting_center_id=meeting_center_id, is_active=True, class_type='Main').first() is not None

    has_extra_classes = Classes.query.filter_by(meeting_center_id=meeting_center_id, is_active=True, class_type='Extra').first() is not None
     
    if not os.path.exists(OUTPUT_DIR):
      os.makedirs(OUTPUT_DIR)  # Crea el directorio si no existe
      
    directory = os.path.join(os.getcwd(), OUTPUT_DIR)
    pdf_files = os.listdir(directory)
    
    return render_template('pdfs/list.html', pdf_files=pdf_files, has_classes=has_classes, has_main_classes=has_main_classes, has_extra_classes=has_extra_classes)


# =============================================================================================
@bp_pdf.route('/generate_all', methods=['GET', 'POST'])
@login_required
def generate_all_pdfs():
    return redirect(url_for('pdf.generate_pdfs', type='todos'))  # redirige a la misma función con parámetro "todos"


# =============================================================================================
@bp_pdf.route('/generate_week', methods=['GET', 'POST'])
@role_required('Admin', 'Super', 'Owner')
def generate_week_pdfs():
    return redirect(url_for('pdf.generate_pdfs', type='semana_especifica'))  # redirige a la misma función para PDFs de la semana específica


# =============================================================================================
@bp_pdf.route('/generate_extra', methods=['GET', 'POST'])
@login_required
def generate_extra_pdfs():
    selected_date = request.form.get('date')  # Obtener la fecha desde el formulario

    # Validar si la fecha fue proporcionada
    if not selected_date:
        flash(_('You must provide a date for this class.'), 'danger')
        return redirect(url_for('pdf.list_classes'))

    # Redirigir a la función generate_pdfs con la fecha como argumento
    return redirect(url_for('pdf.generate_pdfs', type='extra', selected_date=selected_date))


# =============================================================================================
@bp_pdf.route('/generate', methods=['GET', 'POST'])
@login_required
def generate_pdfs():
    user_date = request.args.get('selected_date')
    
    OUTPUT_DIR = get_output_dir()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    def get_class_date(class_type, user_date=None):
        if class_type == 'Main':
            return get_next_sunday()
        elif class_type == 'Extra' and user_date:
            try:
                class_date = datetime.strptime(user_date, '%Y-%m-%d')
                if class_date.date() >= datetime.today().date():
                    return class_date
                else:
                    raise ValueError(_('The date must be today or in the future.'))
            except ValueError as e:
                flash(str(e), 'error')
                return None
        else:
            flash(_('Invalid date for extra class.'), 'error')
            return None

    next_sunday_code  = get_next_sunday_code(get_next_sunday())
    meeting_center_id = session['meeting_center_id']
    unit_name         = session['meeting_center_name']
    unit              = session['meeting_center_number']
    sunday_week       = (get_next_sunday().day - 1) // 7 + 1

    clases_a_imprimir = list({
        c for c in (
            Classes.query.filter_by(is_active=True, meeting_center_id=meeting_center_id)
            if request.args.get('type') == 'todos'
            else Classes.query.filter_by(is_active=True, class_type='Extra', meeting_center_id=meeting_center_id)
            if request.args.get('type') == 'extra'
            else [
                c for c in Classes.query.filter_by(is_active=True, meeting_center_id=meeting_center_id)
                if str(sunday_week) in c.schedule.split(',')
            ]
        )
    })
    clean_qr_folder(OUTPUT_DIR)

    for class_entry in clases_a_imprimir:
        if class_entry.class_type == 'Extra' and not user_date:
            continue

        class_date = get_class_date(class_entry.class_type, user_date)
        if not class_date:
            continue

        class_name  = class_entry.translated_name
        class_code  = class_entry.class_code
        class_color = class_entry.class_color or "black"

        qr_url = f"{Config.BASE_URL}/attendance?className={class_name.replace(' ', '+')}&sundayCode={next_sunday_code}&date={class_date.strftime('%Y-%m-%d')}&unitNumber={unit}&classCode={class_code}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=class_color, back_color="white")

        qr_filename = os.path.join(OUTPUT_DIR, f"{class_name}_{format_date(class_date)}.png")
        img.save(qr_filename)

        pdf_filename = os.path.join(OUTPUT_DIR, f"{_(class_name)}_{format_date(class_date)}.pdf")
        c = canvas.Canvas(pdf_filename, pagesize=letter)

        page_width, page_height = letter
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor("black")
        c.drawCentredString(page_width / 2, 600, _(f"Attendance Sheet"))
        
        rec_x=45
        rec_y=45
        c.rect(rec_x+22, rec_y, (page_width-rec_x * 2)-44, page_height - rec_y * 4)
        
        qr_image = ImageReader(qr_filename)
        qr_size = 442
        qr_x=85
        qr_y=115
        c.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)

        c.setFont("Helvetica-Bold", 35)
        c.drawCentredString(page_width / 2, 560, _(class_name))
        
        c.setFont("Helvetica", 16)
        c.drawCentredString(page_width / 2, 99, unit_name)
        c.drawCentredString(page_width / 2, 74, f"{format_date(class_date)}") 

        c.setLineWidth(0.5)
        c.setDash(5, 10)
        c.line(0, page_height - rec_y * 4 +68, 612, page_height - rec_y * 4 +68)
        c.line(rec_x, 0, rec_x, page_height)
        c.line(567, 0, 567, page_height)
        c.line(0, 22.5, page_width, 22.5)
        c.showPage()
           
        # Segunda página con QR de reset y QR del maestro si ya existe
        # QR para resetear el nombre
        manual_qr_url = f"{Config.BASE_URL}/attendance/manual"
        manual_qr = qrcode.QRCode(version=1, box_size=5, border=2)
        manual_qr.add_data(manual_qr_url)
        manual_qr.make(fit=True)
        manual_img = manual_qr.make_image(fill_color="black", back_color="white")
        manual_qr_filename = os.path.join(OUTPUT_DIR, "manual_attendance.png")
        manual_img.save(manual_qr_filename)

        reset_qr_image = ImageReader(manual_qr_filename)
        c.drawCentredString(page_width / 2, 605, _('Register Manual Attendance'))
        c.drawImage(reset_qr_image, page_width / 2 - 50, 500, width=100, height=100)

        # Verificar si el QR del maestro ya existe
        classes_teacher = {
            "YW": "RS",
            "AP": "EQ",
            "SSY": "SSA"
        }        
        # Obtener el nombre de la clase del maestro usando el código del maestro
        class_teacher = classes_teacher.get(class_code)
        if class_teacher:
            # Buscar la clase asociada al código del maestro
            teacher_class = Classes.query.filter_by(class_code=class_teacher).first()
            
            if teacher_class:
                teacher_class_name = teacher_class.translated_name  # Obtén el nombre de la clase

                # Crear el nombre del archivo para el QR del maestro
                teacher_qr_filename = os.path.join(OUTPUT_DIR, f"{class_teacher}_{format_date(class_date)}.png")

                # Comprobar si el QR del maestro ya existe
                if os.path.exists(teacher_qr_filename):  # Si el QR ya existe, reutilízalo
                    teacher_qr_image = ImageReader(teacher_qr_filename)
                else:  # Si no existe, genera uno nuevo
                    teacher_qr_url = f"{Config.BASE_URL}/attendance?className={teacher_class_name.replace(' ', '+')}&classCode={class_teacher}&date={class_date.strftime('%Y-%m-%d')}&sundayCode={next_sunday_code}&unitNumber={unit}"
                    teacher_qr = qrcode.QRCode(version=1, box_size=10, border=4)
                    teacher_qr.add_data(teacher_qr_url)
                    teacher_qr.make(fit=True)
                    teacher_img = teacher_qr.make_image(fill_color="black", back_color="white")
                    teacher_img.save(teacher_qr_filename)
                    teacher_qr_image = ImageReader(teacher_qr_filename)

                # Dibujar el QR del maestro en la página
                teacher_qr_size = 180
                teacher_qr_x = (page_width - teacher_qr_size) / 2
                teacher_qr_y = 90
                c.drawImage(teacher_qr_image, teacher_qr_x, teacher_qr_y, width=teacher_qr_size, height=teacher_qr_size)
                c.drawCentredString(page_width / 2, teacher_qr_y + teacher_qr_size, _('Teacher\'s Attendance Class'))  # Mostrar el nombre de la clase del maestro
                c.setFont("Helvetica-Bold", 14)
                c.drawCentredString(page_width / 2, teacher_qr_y - 10, teacher_class_name)  # Mostrar el nombre de la clase del maestro

        # Guardar la página PDF
        c.save()

    clean_qr_images(OUTPUT_DIR)
    flash(_('QR Codes generated successfully.'), 'success')
    return redirect(url_for('pdf.list_pdfs'))


# =============================================================================================
@bp_pdf.route('/view/<path:filename>', methods=['GET'])
@login_required
def view_pdf(filename):
    OUTPUT_DIR = get_output_dir()
    try:
        directory = os.path.join(os.getcwd(), OUTPUT_DIR)
        filename = unquote(filename)
        full_path = os.path.join(directory, filename)

        print(f"Trying to access: {full_path}")  # Debugging output

        if not os.path.exists(full_path):
            print("File not found:", full_path)  # More detailed log
            abort(404, description=f"File not found: {filename}")

        return send_from_directory(directory, filename, as_attachment=False)  # Se muestra en el navegador
    except Exception as e:
        print(f"Error: {e}")  # Log the actual error for debugging
        abort(500, description=str(e))
        
        

