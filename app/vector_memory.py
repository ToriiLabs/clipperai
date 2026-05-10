# app/vector_memory.py
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorMemory:
    def __init__(self):
        self.memories: List[Dict[str, Any]] = []

    def add_memory(self, text: str, metadata: Dict[str, Any] = None):
        self.memories.append({
            "text": text.strip(),
            "metadata": metadata or {},
            "timestamp": datetime.utcnow()
        })
        logger.info(f"📌 Clipped to memory: {text[:70]}...")

    def search_memory(self, query: str, n_results: int = 6) -> List[str]:
        if not self.memories:
            return []
        # Simple recency-based retrieval
        return [m["text"] for m in self.memories[-n_results:]]

# ←←← THIS LINE WAS MISSING ←←←
vector_memory = VectorMemory()
