from flask import Flask
from flask_migrate import Migrate
from config import Config
from models import db
from routes import bp as routes_blueprint
# from flask_bootstrap import Bootstrap



app = Flask(__name__)
app.config.from_object(Config)
# bootstrap = Bootstrap(app)

db.init_app(app)
migrate = Migrate(app, db)

# Registro de rutas
app.register_blueprint(routes_blueprint)

migrate = Migrate(app, db)

if __name__ == '__main__':
   with app.app_context():
        db.create_all()
        app.run(debug=True)
