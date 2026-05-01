from flask import Blueprint, request, jsonify, render_template, current_app
import logging
from .ai_model import generate_response, load_model
from .models import db

bp = Blueprint('routes', __name__)
logger = logging.getLogger(__name__)

@bp.before_app_request
def before_request():
    if not hasattr(current_app, 'db_initialized'):
        db.create_all()
        current_app.db_initialized = True
    logging.basicConfig(level=logging.INFO)

# Load model on startup
load_model()

@bp.route('/')
def home():
    return render_template('index.html')

@bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message')
        session_id = data.get('session_id', 'default')

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        response = generate_response(user_message, session_id)

        return jsonify({
            "response": response,
            "session_id": session_id
        })
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": "An error occurred."}), 500
