from flask import Flask
from flask_cors import CORS
from .config import Config
from .models import db

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)
    
    CORS(app)
    db.init_app(app)
    
    from .routes import bp
    app.register_blueprint(bp)
    
    return app
