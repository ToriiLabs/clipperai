# app/config.py
import os
from datetime import timedelta
import torch  # for dtype check

class Config:
    # === IMPORTANT: Change this in production! ===
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-this-in-production-123456789')

    SQLALCHEMY_DATABASE_URI = 'sqlite:///clipperai.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    MAX_HISTORY = 20
    MODEL_PATH = 'Qwen/Qwen2.5-1.5B-Instruct'
    HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")
    
    # Memory & Loading Optimizations
    TORCH_DTYPE = torch.float16 if torch.cuda.is_available() else torch.float32
    LOW_CPU_MEM_USAGE = True
    OFFLOAD_FOLDER = "offload"
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
