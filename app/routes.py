# app/routes.py
from flask import Blueprint, request, jsonify, Response, render_template, current_app
import logging
import os
import json
import asyncio
from .ai_model import generate_with_reflection, get_llm   # ← Updated import
from .rag import process_document
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

@bp.route('/api/chat', methods=['POST'])
def chat():
    """Keep old non-streaming endpoint for backward compatibility"""
    data = request.json
    user_message = data.get('message')
    session_id = data.get('session_id', 'default')
    if not user_message:
        return jsonify({"error": "Message is required"}), 400
    
    # For now we still use the old sync version if it exists, or you can switch it later
    # (reflection is only in the streaming path for best UX)
    response = "Reflection mode only available in streaming for now."
    return jsonify({"response": response, "session_id": session_id})

@bp.route('/api/stream', methods=['POST'])
def stream_chat():
    """Streaming with 32B model + deep reflection (much smarter)"""
    data = request.json
    user_message = data.get('message')
    session_id = data.get('session_id', 'default')

    if not user_message:
        return jsonify({"error": "Message required"}), 400

    def generate():
        try:
            # Run the async reflection logic in the sync Flask generator
            final_text = asyncio.run(generate_with_reflection(user_message, session_id))
            
            # Stream the polished final answer word-by-word (smooth UI feel)
            for token in final_text.split():
                yield f"data: {json.dumps({'token': token + ' '})}\n\n"
                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'token': 'Sorry, something went wrong.'})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

# === SIDEBAR ENDPOINTS (unchanged) ===
@bp.route('/api/history', methods=['GET'])
def get_history():
    sessions = Conversation.query.with_entities(Conversation.session_id).distinct().all()
    return jsonify({"sessions": [s[0] for s in sessions]})

@bp.route('/api/clips', methods=['GET'])
def get_clips():
    clips = vector_memory.get_all_memory()
    return jsonify({"clips": clips})

@bp.route('/api/clear', methods=['POST'])
def clear_all():
    db.session.query(Conversation).delete()
    db.session.commit()
    return jsonify({"status": "cleared"})
