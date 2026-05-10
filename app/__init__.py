# app/__init__.py
from flask import Flask
from flask_cors import CORS
from .config import Config
from .models import db
import os


def create_app(config_class=Config):
    """Application factory - fully fixed version"""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(app_dir)

    app = Flask(__name__,
                template_folder=os.path.join(root_dir, 'templates'),
                static_folder=os.path.join(root_dir, 'static'))

    app.config.from_object(config_class)

    CORS(app)
    db.init_app(app)

    # Register blueprint
    from .routes import bp
    app.register_blueprint(bp)

    # Create DB tables on startup
    with app.app_context():
        db.create_all()
        print("✅ Database initialized (clipperai.db)")

    print("✅ ClipperAI Flask app ready!")
    return app
