# app/routes.py
from flask import Blueprint, request, jsonify, Response, render_template, current_app
import logging
import os
import json
from .ai_model import generate_with_reflection
from .models import db, Conversation
from .vector_memory import VectorMemory

bp = Blueprint('routes', __name__)
logger = logging.getLogger(__name__)
vector_memory = VectorMemory()

UPLOAD_FOLDER = 'data/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@bp.before_app_request
def before_request():
    if not hasattr(current_app, 'db_initialized'):
        with current_app.app_context():
            db.create_all()
            current_app.db_initialized = True

@bp.route('/')
def home():
    return render_template('index.html')

@bp.route('/api/stream', methods=['POST'])
def stream_chat():
    data = request.json
    user_message = data.get('message')
    session_id = data.get('session_id', 'default')

    if not user_message:
        return jsonify({"error": "Message required"}), 400

    def generate():
        try:
            # Show thinking phases (nice UX)
            yield f"data: {json.dumps({'phase': 'thinking', 'text': 'Thinking step-by-step...'})}\n\n"
            yield f"data: {json.dumps({'phase': 'reflecting', 'text': 'Reflecting and polishing...'})}\n\n"

            # Real streaming from the model (Grok-like)
            for token in generate_with_reflection(user_message):
                yield f"data: {json.dumps({'token': token})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'token': f'Error: {str(e)}'})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

# Sidebar endpoints (unchanged)
@bp.route('/api/history', methods=['GET'])
def get_history():
    sessions = Conversation.query.with_entities(Conversation.session_id).distinct().all()
    return jsonify({"sessions": [s[0] for s in sessions]})

@bp.route('/api/clips', methods=['GET'])
def get_clips():
    try:
        clips = vector_memory.get_all_memory()
    except Exception:
        clips = []
    return jsonify({"clips": clips})

@bp.route('/api/clear', methods=['POST'])
def clear_all():
    db.session.query(Conversation).delete()
    db.session.commit()
    return jsonify({"status": "cleared"})
