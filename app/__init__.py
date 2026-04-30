from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__,
                static_url_path='/static',
                static_folder='../static',
                template_folder='../templates')
    
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)
    
    return app
