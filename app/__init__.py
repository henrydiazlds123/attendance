# app/__init__.py
from .config       import Config
from .models       import db, User
from .routes       import register_blueprints
from flask         import Flask, request, session, g
from flask_babel   import Babel, format_datetime
from flask_migrate import Migrate


def get_locale():
    lang = request.args.get('lang')
    if lang and lang in Config.LANGUAGES:
        session['lang'] = lang
        return lang
    
    if 'lang' in session and session['lang'] in Config.LANGUAGES:
        return session['lang']
    
    return request.accept_languages.best_match(Config.LANGUAGES)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configuración de la Base de Datos
    db.init_app(app)
    Migrate(app, db)

    # Inicialización de Babel
    babel = Babel(app, locale_selector=get_locale)

    # **Mover load_user() aquí para manejar autenticación global**
    @app.before_request
    def load_user():
        user_id = session.get('user_id')

        if not user_id:
            user_id = request.cookies.get('remember_me')

        if user_id:
            # Cambiar de User.query.get(user_id) a la sesión
            user = db.session.get(User, user_id)  # Uso de Session.get()
            if user:
                g.user = user
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['role'] = user.role
                session['organization_id'] = user.organization_id

                # ✅ Solo establece 'meeting_center_id' si no existe en la sesión
                if 'meeting_center_id' not in session:
                    session['meeting_center_id'] = user.meeting_center_id  
            else:
                g.user = None
        else:
            g.user = None

    # Registro de Rutas
    register_blueprints(app)

    # Registrar funciones adicionales en Jinja2
    @app.context_processor
    def inject_utilities():
        return {
            'get_locale': get_locale,
            'format_datetime': format_datetime,
        }

    return app

