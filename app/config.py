import os

class Config:
    MAX_HISTORY = 10
    MODEL_PATH = 'google/flan-t5-large'
    HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", "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")
