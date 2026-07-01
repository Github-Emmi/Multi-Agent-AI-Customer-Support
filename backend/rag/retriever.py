import pickle
from pathlib import Path
from typing import List, Dict

import faiss
import numpy as np

from backend.embeddings.encoder import EmbeddingEncoder

INDEX_DIR = Path("vectorstore/faiss_index")


class RAGRetriever:
    """Singleton FAISS-based semantic retriever."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_index()
        return cls._instance

    def _load_index(self):
        if not (INDEX_DIR / "index.faiss").exists():
            self.index = None
            self.metadata = []
            print("WARNING: FAISS index not found. Run the ingestion pipeline first.")
            return
        self.index = faiss.read_index(str(INDEX_DIR / "index.faiss"))
        with open(INDEX_DIR / "metadata.pkl", "rb") as f:
            self.metadata = pickle.load(f)
        self.encoder = EmbeddingEncoder()

    def reload(self):
        """Reload index from disk after re-ingestion."""
        self._load_index()

    def search(self, query: str, top_k: int = 4) -> List[Dict]:
        """Return top-k most relevant chunks for the query."""
        if self.index is None:
            return []

        query_vector = np.array(
            [self.encoder.encode_query(query)]
        ).astype("float32")

        distances, indices = self.index.search(query_vector, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            chunk = self.metadata[idx].copy()
            chunk["score"] = float(dist)
            results.append(chunk)

        return results


retriever = RAGRetriever()
