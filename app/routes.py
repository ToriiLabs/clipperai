from flask import Blueprint, request, jsonify, render_template, current_app
import logging
from .ai_model import generate_response, load_model

bp = Blueprint('routes', __name__)
logger = logging.getLogger(__name__)

@bp.before_app_request
def before_request():
    logging.basicConfig(level=logging.INFO)

# Load model on first request
load_model()

@bp.route('/')
def home():
    return render_template('index.html')

@bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message')
        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        clipper_response = generate_response(user_message)

        return jsonify({
            "conversation": list(conversation_history),
            "response": clipper_response
        })
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": "An error occurred."}), 500
