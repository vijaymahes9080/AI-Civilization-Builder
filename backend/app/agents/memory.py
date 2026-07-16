import numpy as np
from typing import List, Dict, Any
import datetime
from backend.app.config import settings

class MemoryStore:
    """
    Manages vector embeddings and decay weighting for agent memories.
    Combines text semantic search with chronological and importance filters.
    """
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        # In-memory storage for local agent memories
        # List of dicts: {"text": str, "vector": np.ndarray, "importance": float, "tick": int, "created_at": str}
        self.memories: List[Dict[str, Any]] = []
        
        # Load embedding model lazily to speed up boot times
        self._embedding_model = None

    @property
    def embedding_model(self):
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            except Exception:
                # Fallback dummy embedder if package is not installed/loading
                class DummyEmbedder:
                    def encode(self, text: str):
                        # Returns a random normalized vector of size 384
                        vec = np.random.randn(384)
                        return vec / np.linalg.norm(vec)
                self._embedding_model = DummyEmbedder()
        return self._embedding_model

    def add_memory(self, text: str, importance: float, current_tick: int):
        """Add a memory event, generate its embedding vector, and save it"""
        vector = self.embedding_model.encode(text)
        self.memories.append({
            "text": text,
            "vector": vector,
            "importance": float(importance),
            "tick": int(current_tick),
            "created_at": datetime.datetime.utcnow().isoformat()
        })

    def query_memories(self, query: str, current_tick: int, limit: int = 5) -> List[str]:
        """
        Queries memories based on cosine semantic match, recency decay, and importance.
        Decay formula: S_decay = exp(-0.005 * (current_tick - memory_tick))
        Score = cosine_similarity * 0.4 + importance * 0.3 + S_decay * 0.3
        """
        if not self.memories:
            return []

        query_vector = self.embedding_model.encode(query)
        scored_memories = []

        for mem in self.memories:
            # Cosine similarity
            cos_sim = np.dot(query_vector, mem["vector"]) / (
                np.linalg.norm(query_vector) * np.linalg.norm(mem["vector"]) + 1e-9
            )
            
            # Recency decay
            ticks_elapsed = current_tick - mem["tick"]
            decay = np.exp(-0.005 * ticks_elapsed)
            
            # Weighted overall score
            score = (cos_sim * 0.4) + (mem["importance"] / 10.0 * 0.3) + (decay * 0.3)
            scored_memories.append((score, mem["text"]))

        # Sort descending by score
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in scored_memories[:limit]]
