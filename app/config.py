import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///clipperai.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    MAX_HISTORY = 20
    MODEL_PATH = 'google/flan-t5-large'
    HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")
