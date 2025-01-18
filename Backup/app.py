from pyclbr import Class
from urllib.parse import unquote
from flask import Flask, abort, jsonify, request, render_template, redirect, url_for, flash, session, send_from_directory
from models import db, Attendance, Config, User
from functools import wraps
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from forms import UserForm, ResetPasswordForm
import pytz
import os, re
import qrcode
from forms import AttendanceForm



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = 'your_secret_key'

def get_next_sunday():
    """Devuelve la fecha del próximo domingo. Si hoy es domingo, devuelve la fecha de hoy."""
    today = datetime.now().date()
    if today.weekday() == 6:  # 6 es domingo
        return today
    else:
        days_until_sunday = 6 - today.weekday()
        return today + timedelta(days=days_until_sunday)
    
def get_sunday_week(fecha):
    """Determina la semana del mes para una fecha dada."""
    return (fecha.day - 1) // 7 + 1

def get_next_sunday_code(next_sunday):
    start_of_year    = datetime(next_sunday.year, 1, 1).date()
    days_since_start = (next_sunday - start_of_year).days
    sunday_code      = (days_since_start * 73 + 42) % 10000
    return sunday_code

def clean_qr_folder(folder_path):
    """Elimina todos los archivos en la carpeta especificada."""
    if os.path.exists(folder_path):
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)  # Elimina el archivo
            except Exception as e:
                print(f"Error al eliminar {file_path}: {e}")

def clean_qr_images(folder_path):
    for file in os.listdir(folder_path):
        if file.endswith(".png"):
            os.remove(os.path.join(folder_path, file))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debe iniciar sesión para acceder a esta página.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('No tiene permisos para acceder a esta página.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def user_first_name(username):
    # Insert a space before each uppercase letter (except the first one)
    separated_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', username)
    # Split the separated name into words and return the first one
    first_name = separated_name.split()[0]
    return first_name

# Variables Globales
BASE_URL      = "https://attendance.indicegenealogico.com" #Production
#BASE_URL      = "http://127.0.0.1:5000" #local

OUTPUT_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qr_codes') #Production
MOUNTAIN_TZ   = pytz.timezone("America/Denver") # Define Mountain Time Zone
MOUNTAIN_TIME = datetime.now(MOUNTAIN_TZ) # Get the current time in Mountain Time
CURRENT_DATE  = MOUNTAIN_TIME.date() # Use mountain_time.date() to get the date part
NEXT_SUNDAY   = get_next_sunday()
CLASES        = [
    "Cuórum de Elderes",
    "Sacerdocio Aarónico",
    "Sociedad de Socorro",
    "Mujeres Jóvenes",
    "Esc. Dom. Jóvenes",
    "Esc. Dom. Adultos",
    "Quinto Domingo"
]

# Initialize the db with the app
db.init_app(app)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['usuario'] = user_first_name(user.username)
            session['is_admin'] = user.is_admin
            flash('Inicio de sesión exitoso.')
            return redirect(url_for('home'))
        else:
            flash('Credenciales inválidas.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada.')
    return redirect(url_for('home'))


@app.errorhandler(404) 
def not_found(e): 
  return render_template("404.html")


@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    class_name = request.args.get('class')
    sunday_code = request.args.get('code')

    if not class_name or not sunday_code or class_name not in CLASES:
        return render_template('400.html'), 400

    code_verification_setting = Config.query.filter_by(key='code_verification').first()
    code_verification_enabled = code_verification_setting.value if code_verification_setting else 'true'

    if code_verification_enabled == 'false':
        return render_template('attendance.html', class_name=class_name, sunday_code=sunday_code, sunday=NEXT_SUNDAY)
    
    expected_code = get_next_sunday_code(NEXT_SUNDAY)
    if int(sunday_code) == expected_code:
        return render_template('attendance.html', class_name=class_name, sunday_code=sunday_code, sunday=NEXT_SUNDAY)
    else:
        return render_template('403.html'), 403


@app.route('/manual_attendance')
#@login_required
def manual_attendance():
    """Genera enlaces solo para las clases correspondientes al próximo domingo."""

    next_sunday_code = get_next_sunday_code(NEXT_SUNDAY)
    sunday_week      = (NEXT_SUNDAY.day - 1) // 7 + 1  # Determina la semana del mes
    
    # Clases según el domingo
    if sunday_week == 5:
        clases_a_imprimir = ["Quinto Domingo"]
    elif sunday_week in [1, 3]:
        clases_a_imprimir = ["Escuela Dominical Adultos", "Escuela Dominical Jóvenes"]
    elif sunday_week in [2, 4]:
        clases_a_imprimir = ["Cuórum de Elderes", "Sacerdocio Aarónico", "Sociedad de Socorro", "Mujeres Jóvenes"]
    else:
        clases_a_imprimir = []
    
    # Generar enlaces solo para las clases correspondientes
    class_links = {
        class_name: f"{BASE_URL}/attendance?class={class_name.replace(' ', '+')}&code={next_sunday_code}"
        for class_name in clases_a_imprimir
    }

    return render_template('manual_attendance.html', class_links=class_links)



@app.route('/registrar', methods=['POST'])
def registrar():
    try:
        student_name     = request.form.get('studentName').title()
        nombre, apellido = student_name.split(" ", 1)
        formatted_name   = f"{apellido}, {nombre}"
        class_name       = request.form.get('className')
        sunday_date      = NEXT_SUNDAY
        sunday_code      = request.form.get('sunday_code')

        # Verificar si la clase es válida
        if class_name not in CLASES:
            return jsonify({
                "success": False,
                "message": "La clase seleccionada no es válida.",
            }), 400

        # Extraer mes y año directamente de la fecha
        month = NEXT_SUNDAY.month
        year  = NEXT_SUNDAY.year

        # Verificar si ya existe un registro
        existing_attendance = Attendance.query.filter_by(student_name=formatted_name, sunday_date=sunday_date).first()

        if existing_attendance:
            return jsonify({
                "success"     : False,
                "message"     : "El estudiante ya tiene un registro para esta clase y fecha.",
                "nombre"      : nombre,
                "sunday_date" : sunday_date.strftime("%b %d, %Y")
            }), 400

        # Registrar la asistencia
        new_attendance = Attendance(student_name=formatted_name, class_name=class_name, sunday_date=sunday_date, sunday_code=sunday_code, month=month, year=year)
        db.session.add(new_attendance)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Asistencia registrada exitosamente.",
            "student_name": student_name,
            "class_name": class_name,
            "sunday_date": sunday_date.strftime("%b %d, %Y")
        }), 200

    except Exception as e:
        # En caso de cualquier error
        return jsonify({
            "success": False,
            "message": f"Hubo un error al registrar la asistencia: {str(e)}"
        }), 500


# Rutas para la Administracion de Asistencias
@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
   
    classes  = db.session.query(Attendance.class_name.distinct()).all()
    students = db.session.query(Attendance.student_name.distinct()).all()
    sundays  = db.session.query(Attendance.sunday_date.distinct()).all()
    years    = db.session.query(Attendance.year.distinct()).all()
    months   = db.session.query(Attendance.month.distinct()).all()

    class_name   = request.args.get('class_name')
    student_name = request.args.get('student_name')
    sunday_date  = request.args.get('sunday_date')
    month        = request.args.get('month')
    year         = request.args.get('year')

    # Obtén la configuración actual
    code_verification_setting = Config.query.filter_by(key='code_verification').first()

    query = Attendance.query

    if class_name:
        query = query.filter(Attendance.class_name.ilike(f'%{class_name}%'))
    if student_name:
        query = query.filter(Attendance.student_name.ilike(f'%{student_name}%'))
    if sunday_date:
        try:
            date_filter = datetime.strptime(sunday_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.sunday_date == date_filter)
        except ValueError:
            pass
    if month:
        query = query.filter(Attendance.month.ilike(f'%{month}%'))
    if year:
        query = query.filter(Attendance.year.ilike(f'%{year}%'))
    
    asistencias = query.order_by(Attendance.student_name, Attendance.sunday_date, Attendance.class_name).all()
    total_registros = len(asistencias)
    has_records = Attendance.query.count() > 0  # Verifica si hay registros

    if request.method == 'POST':
        # Manejar cambio en la verificación de código
        if 'code_verification' in request.form:
            new_value = request.form.get('code_verification')
            if code_verification_setting:
                code_verification_setting.value = new_value
            else:
                code_verification_setting = Config(key='code_verification', value=new_value)
                db.session.add(code_verification_setting)
            db.session.commit()

        if 'delete_selected' in request.form:
            ids_to_delete = request.form.getlist('delete')
            for id in ids_to_delete:
                attendance = Attendance.query.get(id)
                if attendance:
                    db.session.delete(attendance)
            db.session.commit()

        elif 'delete_all' in request.form:
            db.session.query(Attendance).delete()
            db.session.commit()

        return redirect(url_for('home'))
    
    verification_enabled = code_verification_setting.value if code_verification_setting else 'true'
    return render_template('index.html', asistencias=asistencias, verification_enabled=verification_enabled, has_records=has_records, classes=classes, students=students, sundays=sundays, months=months, years=years, total_registros=total_registros)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    return redirect(url_for('home'))
    


@app.route('/borrar_asistencia/<int:id>', methods=['GET'])
@admin_required
def borrar_asistencia(id):
    try:
        asistencia = Attendance.query.get(id)
        if asistencia:
            db.session.delete(asistencia)
            db.session.commit()
        return redirect(url_for('admin'))
    except Exception as e:
        print(f"Error al borrar asistencia: {e}")
        return redirect(url_for('admin'))

# Rutas para la Administracion de PDF
@app.route('/list_pdfs', methods=['GET'])
@login_required
def list_pdfs():
    directory = os.path.join(os.getcwd(), OUTPUT_DIR)
    pdf_files = os.listdir(directory)
    return render_template('list_pdfs.html', pdf_files=pdf_files)


# Botones en la interfaz para generar PDFs:
@app.route('/generate_all_pdfs', methods=['GET', 'POST'])
def generate_all_pdfs():
    return redirect(url_for('generate_pdfs', type='todos'))  # redirige a la misma función con parámetro "todos"

@app.route('/generate_week_pdfs', methods=['GET', 'POST'])
def generate_week_pdfs():
    return redirect(url_for('generate_pdfs', type='semana_especifica'))  # redirige a la misma función para PDFs de la semana específica


@app.route('/generate_pdfs', methods=['GET', 'POST'])
def generate_pdfs():
    """Genera PDFs con códigos QR para las clases correspondientes a un domingo específico."""
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Verificar si el usuario quiere todos los PDFs o solo los de la semana específica
    if request.args.get('type') == 'todos':
        clases_a_imprimir = CLASES
    else:
        sunday_week = get_sunday_week(NEXT_SUNDAY)
        
        # Definir las clases según la semana del mes
        if sunday_week == 5:
            clases_a_imprimir = ["Quinto Domingo"]
        elif sunday_week in [1, 3]:
            clases_a_imprimir = ["Esc. Dom. Adultos", "Esc. Dom. Jóvenes"]
        elif sunday_week in [2, 4]:
            clases_a_imprimir = ["Cuórum de Elderes", "Sacerdocio Aarónico", "Sociedad de Socorro", "Mujeres Jóvenes"]
        else:
            clases_a_imprimir = []
    
    next_sunday_code = get_next_sunday_code(NEXT_SUNDAY)
    
    clean_qr_folder(OUTPUT_DIR)
    
    for class_name in clases_a_imprimir:
        qr_url = f"{BASE_URL}/attendance?class={class_name.replace(' ', '+')}&code={next_sunday_code}"
        
        # Crear código QR
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar imagen QR
        qr_filename = os.path.join(OUTPUT_DIR, f"{class_name}_{NEXT_SUNDAY}.png")
        img.save(qr_filename)
        
        # Crear PDF
        pdf_filename = os.path.join(OUTPUT_DIR, f"{class_name}_{NEXT_SUNDAY}.pdf")
        c = canvas.Canvas(pdf_filename, pagesize=letter)
        page_width, page_height = letter
        
        # Título del PDF
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(page_width / 2, 670, f"Lista de Asistencia")
        c.setFont("Helvetica-Bold", 35)
        c.drawCentredString(page_width / 2, 625, class_name)
        
        # Insertar el código QR
        qr_image = ImageReader(qr_filename)
        qr_size = 450
        qr_x = (page_width - qr_size) / 2
        qr_y = (page_height - qr_size) / 2
        c.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)
        
        # Fecha de la clase
        c.setFont("Helvetica", 18)
        c.drawCentredString(page_width / 2, qr_y - 15, f"Fecha: {NEXT_SUNDAY}")
        
        c.save()

    clean_qr_images(OUTPUT_DIR)
    print(f"Archivos PDFs generados para el domingo {NEXT_SUNDAY} con código {next_sunday_code}.")
    
    return redirect(url_for('list_pdfs'))



@app.route('/download_pdf/<path:filename>', methods=['GET'])
def download_pdf(filename):
    try:
        directory = os.path.join(os.getcwd(), OUTPUT_DIR)
        filename = unquote(filename)
        full_path = os.path.join(directory, filename)

        print(f"Trying to download from: {full_path}")  # Debugging output

        if not os.path.exists(full_path):
            print("File not found:", full_path)  # More detailed log
            abort(404, description=f"File not found: {filename}")

        return send_from_directory(directory, filename, as_attachment=True)
    except Exception as e:
        print(f"Error: {e}")  # Log the actual error for debugging
        abort(500, description=str(e))



@app.route('/users', methods=['GET'])
@admin_required
def list_users():
    if not session.get('is_admin'):
        return redirect(url_for('home'))
    users = User.query.all()
    admin_count = User.query.filter_by(is_admin=True).count()
    return render_template('users.html', users=users, admin_count=admin_count)

@app.route('/users/new', methods=['GET', 'POST'])
@admin_required
def create_user():
    if not session.get('is_admin'):
        return redirect(url_for('home'))
    form = UserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, is_admin=form.is_admin.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Usuario creado exitosamente.')
        return redirect(url_for('list_users'))
    return render_template('user_form.html', form=form)

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    if not session.get('is_admin'):
        return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.is_admin = form.is_admin.data
        db.session.commit()
        flash('Usuario actualizado exitosamente.')
        return redirect(url_for('list_users'))
    return render_template('user_form.html', form=form)

@app.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    if not session.get('is_admin'):
        return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    admin_count = User.query.filter_by(is_admin=True).count()
    
    if user.is_admin and admin_count <= 1:
        flash('No puedes eliminar al último administrador.', 'error')
        return redirect(url_for('list_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado exitosamente.', 'success')
    return redirect(url_for('list_users'))

@app.route('/users/<int:user_id>/reset_password', methods=['GET', 'POST'])
@admin_required
def reset_password(user_id):
    if not session.get('is_admin'):
        return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Contraseña restablecida exitosamente.')
        return redirect(url_for('list_users'))
    return render_template('reset_password.html', form=form, user=user)


@app.route('/users/<int:user_id>/promote', methods=['POST'])
@admin_required
def promote_to_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('El usuario ya es administrador.', 'info')
    else:
        user.is_admin = True
        db.session.commit()
        flash(f'El usuario {user.username} ha sido promovido a administrador.', 'success')
    return redirect(url_for('list_users'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True)