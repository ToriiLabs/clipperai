# app/routes.py
from flask import Blueprint, request, jsonify, Response, render_template
import logging
import json
import os
from werkzeug.utils import secure_filename
from .ai_model import generate_with_reflection
from .models import db, Conversation
from .rag import process_document
from .vector_memory import vector_memory

bp = Blueprint('routes', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
def home():
    return render_template('index.html')

@bp.route('/api/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        result = process_document(file_path, filename)
        return jsonify({"status": "success", "message": result})
    return jsonify({"error": "Upload failed"}), 500

@bp.route('/api/stream', methods=['POST'])
def stream_chat():
    data = request.json
    user_message = data.get('message')
    if not user_message:
        return jsonify({"error": "Message required"}), 400

    def generate():
        try:
            for chunk in generate_with_reflection(user_message):
                if chunk.startswith("PHASE:"):
                    phase = chunk.split(":", 1)[1].strip().lower()
                    yield f"data: {json.dumps({'phase': phase})}\n\n"
                elif chunk.startswith("TOKEN:"):
                    token = chunk.split(":", 1)[1]
                    yield f"data: {json.dumps({'token': token})}\n\n"
                else:
                    yield f"data: {json.dumps({'token': str(chunk)})}\n\n"
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'phase': 'final'})}\n\n"
            yield f"data: {json.dumps({'token': f'Error: {str(e)}'})}\n\n"

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
        # Semantic search for recent/relevant clips
        clips = vector_memory.search_memory("summary of my documents and knowledge", n_results=12)
        clips = [c[:120] + "..." for c in clips]
        return jsonify({"clips": clips})
    except Exception as e:
        logger.error(f"Clips error: {e}")
        return jsonify({"clips": []})

@bp.route('/api/clear', methods=['POST'])
def clear_all():
    try:
        db.session.query(Conversation).delete()
        vector_memory.clear()
        db.session.commit()
        return jsonify({"status": "cleared"})
    except Exception as e:
        logger.error(f"Clear error: {e}")
        return jsonify({"error": str(e)}), 500
