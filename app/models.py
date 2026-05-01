from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import chromadb
from chromadb.config import Settings
import uuid

db = SQLAlchemy()

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class VectorMemory:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="data/chroma")
        self.collection = self.client.get_or_create_collection(
            name="clipperai_memory",
            metadata={"hnsw:space": "cosine"}
        )

    def add_memory(self, text: str, metadata: dict = None):
        if metadata is None:
            metadata = {}
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[str(uuid.uuid4())]
        )

    def search_memory(self, query: str, n_results: int = 5):
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results.get('documents', [[]])[0]
