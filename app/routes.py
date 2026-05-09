# app/routes.py
from flask import Blueprint, request, jsonify, Response, render_template, current_app
import logging
import json
from .ai_model import generate_with_reflection

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
        for chunk in generate_with_reflection(user_message):
            if chunk.startswith("PHASE:"):
                phase = chunk.split(":", 1)[1]
                if phase == "THINKING":
                    yield f"data: {json.dumps({'phase': 'thinking', 'text': '🧠 Thinking step-by-step...'})} \n\n"
                elif phase == "REFLECTING":
                    yield f"data: {json.dumps({'phase': 'reflecting', 'text': '🔄 Reflecting & polishing...'})} \n\n"
                elif phase == "FINAL":
                    yield f"data: {json.dumps({'phase': 'final', 'text': ''})} \n\n"
                elif phase == "ERROR":
                    yield f"data: {json.dumps({'error': chunk.split('\n', 1)[1]})} \n\n"
            else:
                # Stream the actual content
                if chunk.startswith("THINKING:"):
                    text = chunk[9:]
                    yield f"data: {json.dumps({'thinking': text})} \n\n"
                elif chunk.startswith("FINAL:"):
                    yield f"data: {json.dumps({'token': chunk[6:]})} \n\n"

    return Response(generate(), mimetype='text/event-stream')
