# app/routes.py
from flask import Blueprint, request, jsonify, Response, render_template, current_app
import logging
import json
from .ai_model import generate_with_reflection
from .models import db, Conversation
from .vector_memory import vector_memory

bp = Blueprint('routes', __name__)
logger = logging.getLogger(__name__)


@bp.route('/')
def home():
    return render_template('index.html')


@bp.route('/api/stream', methods=['POST'])
def stream_chat():
    data = request.json
    user_message = data.get('message')
    if not user_message:
        return jsonify({"error": "Message required"}), 400

    def generate():
        # Send phases + tokens exactly as frontend expects
        for chunk in generate_with_reflection(user_message):
            if chunk.startswith("PHASE:"):
                phase = chunk.split(":", 1)[1].strip().lower()
                yield f"data: {json.dumps({'phase': phase})}\n\n"
            elif chunk.startswith("TOKEN:"):
                token = chunk.split(":", 1)[1]
                yield f"data: {json.dumps({'token': token})}\n\n"
            else:
                # fallback text
                yield f"data: {json.dumps({'token': chunk})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@bp.route('/api/history')
def get_history():
    sessions = db.session.query(Conversation.session_id).distinct().all()
    sessions = [s[0] for s in sessions]
    return jsonify({"sessions": sessions})


@bp.route('/api/clips')
def get_clips():
    clips = [m["text"][:120] + "..." for m in vector_memory.memories[-12:]]
    return jsonify({"clips": clips})


@bp.route('/api/clear', methods=['POST'])
def clear_all():
    try:
        db.session.query(Conversation).delete()
        vector_memory.memories.clear()
        db.session.commit()
        return jsonify({"status": "cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
