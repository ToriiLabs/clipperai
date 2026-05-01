from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Lazy VectorMemory - don't create at import time
class VectorMemory:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            import chromadb
            cls._instance = chromadb.PersistentClient(path="data/chroma")
            cls._instance.get_or_create_collection(
                name="clipperai_memory",
                metadata={"hnsw:space": "cosine"}
            )
        return cls._instance

    @classmethod
    def add_memory(cls, text: str, metadata: dict = None):
        if metadata is None:
            metadata = {}
        client = cls.get_instance()
        collection = client.get_collection("clipperai_memory")
        collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[str(uuid.uuid4())]
        )

    @classmethod
    def search_memory(cls, query: str, n_results: int = 5):
        client = cls.get_instance()
        collection = client.get_collection("clipperai_memory")
        results = collection.query(query_texts=[query], n_results=n_results)
        return results.get('documents', [[]])[0]
