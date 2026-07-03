"""
Retriever factory — returns FAISS or Pinecone retriever based on VECTOR_STORE env var.
Usage: from backend.rag.retriever_factory import get_retriever
"""
from functools import lru_cache
from typing import List, Dict


def get_retriever():
    """
    Return the active retriever based on VECTOR_STORE config.
    - "faiss" (default, local dev): loads index from vectorstore/faiss_index/
    - "pinecone" (production): connects to Pinecone cloud index
    """
    from backend.config import settings

    if settings.VECTOR_STORE == "pinecone":
        from backend.vectorstore.pinecone_store import PineconeStore
        return PineconeStore()
    else:
        from backend.rag.retriever import retriever
        return retriever
