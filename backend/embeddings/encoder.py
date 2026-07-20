import asyncio
from typing import List

from sentence_transformers import SentenceTransformer

from backend.config import settings

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingEncoder:
    """Singleton sentence-transformer encoder.

    In production we only ever embed a single user query (one short string).
    The heavy work of embedding the whole knowledge base is done OFFLINE in the
    Kaggle Factory (see documentations/13_KAGGLE_FACTORY_PATTERN.md), so it never
    touches the request path.

    The device is forced via settings.EMBEDDING_DEVICE (default "cpu"). Pinning
    to CPU avoids the Apple-Silicon MPS resource-cleanup segfault that occurs on
    interpreter shutdown, and keeps embedding deterministic across environments.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model = SentenceTransformer(
                MODEL_NAME,
                device=settings.EMBEDDING_DEVICE,
            )
        return cls._instance

    def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress_bar: bool = False,
    ) -> List[List[float]]:
        """Embed a batch of texts.

        Progress bar defaults to OFF: the tqdm "Batches: 0%" render is what made
        the async chat endpoint appear to hang. Offline ingestion may pass
        show_progress_bar=True explicitly.
        """
        return self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
        ).tolist()

    def encode_query(self, query: str) -> List[float]:
        """Embed a single query string (synchronous, no progress bar)."""
        return self.model.encode([query], show_progress_bar=False)[0].tolist()

    async def aencode_query(self, query: str) -> List[float]:
        """Async query embedding.

        SentenceTransformer.encode() is a synchronous, CPU-bound call. Running it
        directly inside an async endpoint blocks the event loop; here we offload
        it to the default thread-pool executor so the loop stays responsive.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.encode_query, query)
