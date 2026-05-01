# app/routes.py
from flask import Blueprint, request, jsonify, render_template, current_app
import logging
import os
from .ai_model import generate_response   # removed load_model import
from .rag import process_document
from .models import db

bp = Blueprint('routes', __name__)
logger = logging.getLogger(__name__)

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
    try:
        data = request.json
        user_message = data.get('message')
        session_id = data.get('session_id', 'default')

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        response = generate_response(user_message, session_id)
        return jsonify({"response": response, "session_id": session_id})
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": "An error occurred."}), 500

@bp.route('/api/upload', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        result = process_document(file_path, file.filename)
        return jsonify({"message": result})
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"error": "Upload failed"}), 500
