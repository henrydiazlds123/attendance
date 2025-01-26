# from flask import Flask, request
# from flask_babel import Babel
# from flask_migrate import Migrate
# from config import Config
# from models import db

# from routes import bp as routes_blueprint
# from flask_bootstrap import Bootstrap


# def get_locale():
#     # Intentar obtener el idioma de una cookie o de la URL
#     lang = request.cookies.get('lang')
#     if lang in app.config['LANGUAGES']:
#         return lang
#     return request.accept_languages.best_match(app.config['LANGUAGES'])


# app = Flask(__name__)
# app.config.from_object(Config)

# Bootstrap(app)

# babel = Babel(app, locale_selector=get_locale)

# app.config['BABEL_DEFAULT_LOCALE'] = 'en'
# app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'




# db.init_app(app)
# migrate = Migrate(app, db)

# # Registro de rutas
# app.register_blueprint(routes_blueprint)


# if __name__ == '__main__':
#    with app.app_context():
#         db.create_all()
#         app.run(debug=True)

from flask import Flask, request
from flask_babel import Babel
from flask_migrate import Migrate
from config import Config
from models import db
from routes import bp as routes_blueprint
from flask_bootstrap import Bootstrap

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configuración de Bootstrap
    Bootstrap(app)

    # Configuración de Babel
    babel = Babel(app, locale_selector=get_locale)
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

    # Configuración de la Base de Datos
    db.init_app(app)
    Migrate(app, db)

    # Registro de Rutas
    app.register_blueprint(routes_blueprint)

    return app

def get_locale():
    # Fuerza un idioma específico para pruebas
    forced_language = 'es'  # Cambia a 'pt' o cualquier otro idioma que quieras probar
    if forced_language in Config.LANGUAGES:
        return forced_language

    # Obtén el idioma desde cookies, la URL o el encabezado Accept-Language
    lang = request.cookies.get('lang')
    if lang in Config.LANGUAGES:
        return lang
    return request.accept_languages.best_match(Config.LANGUAGES)

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
