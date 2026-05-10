# app/routes.py
from flask import Blueprint, request, jsonify, Response, render_template
import logging
import json
from .ai_model import generate_with_reflection
from .models import db, Conversation

bp = Blueprint('routes', name='routes', __name__)
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
        try:
            # Stream phases and tokens from ai_model
            for chunk in generate_with_reflection(user_message):
                if chunk.startswith("PHASE:"):
                    phase = chunk.split(":", 1)[1].strip().lower()
                    yield f"data: {json.dumps({'phase': phase})}\n\n"
                
                elif chunk.startswith("TOKEN:"):
                    token = chunk.split(":", 1)[1]
                    yield f"data: {json.dumps({'token': token})}\n\n"
                
                else:
                    # Fallback for any raw text
                    yield f"data: {json.dumps({'token': chunk})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'phase': 'final'})}\n\n"
            yield f"data: {json.dumps({'token': f'❌ Server error: {str(e)}'})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@bp.route('/api/history')
def get_history():
    try:
        sessions = db.session.query(Conversation.session_id).distinct().all()
        sessions = [s[0] for s in sessions]
        return jsonify({"sessions": sessions})
    except Exception as e:
        logger.error(f"History error: {e}")
        return jsonify({"sessions": []})


@bp.route('/api/clips')
def get_clips():
    try:
        from .vector_memory import vector_memory
        clips = [m["text"][:120] + "..." for m in vector_memory.memories[-12:]]
        return jsonify({"clips": clips})
    except Exception as e:
        logger.error(f"Clips error: {e}")
        return jsonify({"clips": []})


@bp.route('/api/clear', methods=['POST'])
def clear_all():
    try:
        db.session.query(Conversation).delete()
        from .vector_memory import vector_memory
        vector_memory.memories.clear()
        db.session.commit()
        return jsonify({"status": "cleared"})
    except Exception as e:
        logger.error(f"Clear error: {e}")
        return jsonify({"error": str(e)}), 500
