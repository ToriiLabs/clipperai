from flask import Blueprint, request, jsonify, render_template, current_app
import logging
import os

bp = Blueprint('routes', __name__)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = 'data/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Lazy imports - moved here so they don't run on startup
def get_ai_functions():
    from .ai_model import generate_response, load_model
    from .agent import agent
    from .models import db
    from .rag import process_document
    return generate_response, load_model, agent, db, process_document

@bp.before_app_request
def before_request():
    if not hasattr(current_app, 'db_initialized'):
        from .models import db
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

        generate_response, _, agent, _, _ = get_ai_functions()
        
        result = agent.invoke({"messages": [user_message]})
        response = result["messages"][-1]

        return jsonify({"response": response, "session_id": session_id})
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"error": "An error occurred. Please try again."}), 500

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

        _, _, _, _, process_document = get_ai_functions()
        result = process_document(file_path, file.filename)
        return jsonify({"message": result})
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"error": "Upload failed"}), 500
