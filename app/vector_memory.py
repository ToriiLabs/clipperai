# app/vector_memory.py
import chromadb
import requests
import logging
import os
from typing import List, Dict, Any
from uuid import uuid4
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorMemory:
    def __init__(self, persist_dir="./data/chroma", collection_name="clipper_memories", embedding_model="nomic-embed-text"):
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.embedding_model = embedding_model
        logger.info(f"✅ ChromaDB vector store initialized with collection '{collection_name}' using {embedding_model} embeddings.")

    def _get_embedding(self, text: str) -> List[float]:
        try:
            response = requests.post(
                "http://localhost:11434/api/embeddings",
                json={"model": self.embedding_model, "prompt": text},
                timeout=30
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Embedding error: {str(e)[:100]}...")
            return [0.0] * 768  # fallback for nomic-embed-text dim

    def add_memory(self, text: str, metadata: Dict[str, Any] = None):
        if not text or not text.strip():
            return
        text = text.strip()
        embedding = self._get_embedding(text)
        meta = metadata or {}
        meta["timestamp"] = datetime.utcnow().isoformat()
        doc_id = str(uuid4())
        self.collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[meta],
            ids=[doc_id]
        )
        logger.info(f"Clipped to vector DB: {text[:70]}...")

    def search_memory(self, query: str, n_results: int = 6) -> List[str]:
        if not query or not query.strip():
            return []
        query_emb = self._get_embedding(query)
        try:
            results = self.collection.query(
                query_embeddings=[query_emb],
                n_results=n_results,
                include=["documents"]
            )
            return results.get("documents", [[]])[0]
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []

    def clear(self):
        try:
            self.client.delete_collection(self.collection.name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection.name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Vector DB cleared.")
        except Exception as e:
            logger.error(f"Clear error: {e}")

# Singleton
vector_memory = VectorMemory()
