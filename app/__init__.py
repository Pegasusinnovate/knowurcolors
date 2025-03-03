from flask import Flask
from flask_wtf.csrf import CSRFProtect
from .scheduler import init_scheduler
from .routes import main_blueprint
from config import Config

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)

    # Setup CSRF protection for all forms
    csrf = CSRFProtect(app)

    # Register routes (blueprints)
    app.register_blueprint(main_blueprint)

    # Initialize background scheduler (auto deletion of old files)
    init_scheduler(app)

    return app