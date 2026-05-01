import os
from datetime import timedelta

class Config:
    # === IMPORTANT: Change this in production! ===
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-this-in-production-123456789')

    SQLALCHEMY_DATABASE_URI = 'sqlite:///clipperai.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    MAX_HISTORY = 20
    MODEL_PATH = 'google/flan-t5-large'
    HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")
    
    # Optional: Make sessions last longer
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
