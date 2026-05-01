# app/vector_memory.py
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class VectorMemory:
    def __init__(self):
        self.memories: List[Dict[str, Any]] = []

    def add_memory(self, text: str, metadata: Dict[str, Any] = None):
        self.memories.append({
            "text": text,
            "metadata": metadata or {},
            "timestamp": __import__('datetime').datetime.utcnow()
        })
        logger.info(f"Added memory clip: {text[:80]}...")

    def search_memory(self, query: str, n_results: int = 5) -> List[str]:
        if not self.memories:
            return []
        # Simple recency-based for now (can upgrade to embeddings later)
        return [m["text"] for m in self.memories[-n_results:]]
