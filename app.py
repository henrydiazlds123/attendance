from flask import Flask, request, session
from flask_babel import Babel, format_datetime
from flask_migrate import Migrate
from config import Config
from models import db
from routes import bp as routes_blueprint

def get_locale():
    # Prioriza el parámetro 'lang' en la URL
    lang = request.args.get('lang')
    if lang and lang in Config.LANGUAGES:
        session['lang'] = lang  # Guarda el idioma en la sesión
        return lang
    
    # Si no hay parámetro 'lang', usa el idioma en la sesión
    if 'lang' in session and session['lang'] in Config.LANGUAGES:
        return session['lang']
    
    # Como último recurso, usa el encabezado Accept-Language
    return request.accept_languages.best_match(Config.LANGUAGES)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configuración de la Base de Datos
    db.init_app(app)
    Migrate(app, db)

    # Inicialización de Babel con el locale_selector
    babel = Babel(app, locale_selector=get_locale)

    # Registro de Rutas
    app.register_blueprint(routes_blueprint)

    # Registrar funciones adicionales en Jinja2
    @app.context_processor
    def inject_utilities():
        return {
            'get_locale': get_locale,
            'format_datetime': format_datetime,  # Asegura que esté disponible en las plantillas
        }
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

