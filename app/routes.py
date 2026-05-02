# app/routes.py
from flask import Blueprint, request, jsonify, Response, render_template, current_app
import logging
import os
import json
from .ai_model import generate_response, get_llm
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
    # Keep your old non-streaming endpoint working
    data = request.json
    user_message = data.get('message')
    session_id = data.get('session_id', 'default')
    if not user_message:
        return jsonify({"error": "Message is required"}), 400
    response = generate_response(user_message, session_id)
    return jsonify({"response": response, "session_id": session_id})

@bp.route('/api/stream', methods=['POST'])
def stream_chat():
    """New real streaming endpoint"""
    data = request.json
    user_message = data.get('message')
    session_id = data.get('session_id', 'default')

    if not user_message:
        return jsonify({"error": "Message required"}), 400

    def generate():
        memory_clips = vector_memory.search_memory(user_message, n_results=8)
        memory_context = "\n\n".join(memory_clips) if memory_clips else "No relevant memory clips."

        system_prompt = "You are ClipperAI — a sharp, creative, honest brainstorming partner. Always prioritize the Memory clips below."

        full_response = ""
        for chunk in get_llm().stream([SystemMessage(content=system_prompt), HumanMessage(content=f"Memory clips:\n{memory_context}\n\nQuestion: {user_message}")]):
            token = chunk.content
            full_response += token
            yield f"data: {json.dumps({'token': token})}\n\n"

        # Save full response to DB after streaming
        try:
            conv = Conversation(session_id=session_id, user_message=user_message, ai_response=full_response)
            db.session.add(conv)
            db.session.commit()
        except Exception:
            db.session.rollback()

    return Response(generate(), mimetype='text/event-stream')

# === SIDEBAR ENDPOINTS ===
@bp.route('/api/history', methods=['GET'])
def get_history():
    sessions = Conversation.query.with_entities(Conversation.session_id).distinct().all()
    return jsonify({"sessions": [s[0] for s in sessions]})

@bp.route('/api/clips', methods=['GET'])
def get_clips():
    clips = vector_memory.get_all_memory()  # assumes you have this method
    return jsonify({"clips": clips})

@bp.route('/api/clear', methods=['POST'])
def clear_all():
    db.session.query(Conversation).delete()
    db.session.commit()
    return jsonify({"status": "cleared"})
