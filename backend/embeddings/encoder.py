from typing import List
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingEncoder:
    """Singleton sentence-transformer encoder."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model = SentenceTransformer(MODEL_NAME)
        return cls._instance

    def encode(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, show_progress_bar=True).tolist()

    def encode_query(self, query: str) -> List[float]:
        return self.model.encode([query])[0].tolist()
