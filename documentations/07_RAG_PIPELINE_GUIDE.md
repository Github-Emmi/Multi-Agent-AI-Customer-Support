# 07 — RAG Pipeline Guide

> **Project:** Multi-Agent AI Customer Support Assistant  
> **Embedding Model:** sentence-transformers/all-MiniLM-L6-v2  
> **Vector Store:** FAISS (dev) / Pinecone (prod)

---

## RAG Pipeline Overview

```
knowledge_base/*.pdf
        │
        ▼  [PyPDF2]
Extract raw text per page
        │
        ▼  [LangChain RecursiveCharacterTextSplitter]
Split into chunks
  - chunk_size: 500 characters
  - chunk_overlap: 50 characters
  - Each chunk retains: source_file, page_number, chunk_id
        │
        ▼  [SentenceTransformer: all-MiniLM-L6-v2]
Generate 384-dimensional embedding vector per chunk
        │
        ▼  [FAISS IndexFlatL2]
Store embedding vectors + metadata
        │
        ▼
Persist index to: vectorstore/faiss_index/
        │
───────────────────────────────────────────────────
        │
        │  [At query time]
        │
        ▼
User query → embed query → 384-dim vector
        │
        ▼  [FAISS similarity search]
Find top-k nearest chunks (k=4 per agent)
        │
        ▼
Return chunks with metadata
        │
        ▼
Inject into agent prompt as [CONTEXT]
```

---

## backend/rag/pipeline.py

```python
import os
import json
import pickle
from pathlib import Path
import faiss
import numpy as np
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from backend.embeddings.encoder import EmbeddingEncoder

KNOWLEDGE_BASE_DIR = Path("knowledge_base")
INDEX_DIR = Path("vectorstore/faiss_index")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def ingest_documents():
    """Load all PDFs, chunk, embed, and build FAISS index."""
    encoder = EmbeddingEncoder()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    all_chunks = []
    all_metadata = []

    for pdf_path in KNOWLEDGE_BASE_DIR.glob("*.pdf"):
        print(f"Processing: {pdf_path.name}")
        reader = PdfReader(str(pdf_path))

        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if not text.strip():
                continue

            chunks = splitter.split_text(text)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metadata.append({
                    "source": pdf_path.name,
                    "page": page_num + 1,
                    "chunk_id": f"{pdf_path.stem}_{page_num}_{i}",
                    "text": chunk,
                })

    print(f"Total chunks: {len(all_chunks)}")

    # Generate embeddings
    embeddings = encoder.encode(all_chunks)
    embeddings_np = np.array(embeddings).astype("float32")

    # Build FAISS index
    dimension = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_np)

    # Persist
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_DIR / "index.faiss"))
    with open(INDEX_DIR / "metadata.pkl", "wb") as f:
        pickle.dump(all_metadata, f)

    print(f"Index saved to {INDEX_DIR}")


if __name__ == "__main__":
    ingest_documents()
```

---

## backend/embeddings/encoder.py

```python
from sentence_transformers import SentenceTransformer
from typing import List

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

class EmbeddingEncoder:
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
```

---

## backend/rag/retriever.py

```python
import pickle
import faiss
import numpy as np
from pathlib import Path
from typing import List, Dict
from backend.embeddings.encoder import EmbeddingEncoder

INDEX_DIR = Path("vectorstore/faiss_index")

class RAGRetriever:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_index()
        return cls._instance

    def _load_index(self):
        self.index = faiss.read_index(str(INDEX_DIR / "index.faiss"))
        with open(INDEX_DIR / "metadata.pkl", "rb") as f:
            self.metadata = pickle.load(f)
        self.encoder = EmbeddingEncoder()

    def search(self, query: str, top_k: int = 4) -> List[Dict]:
        """Return top-k most relevant chunks for the query."""
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


# Singleton retriever
retriever = RAGRetriever()
```

---

## backend/vectorstore/faiss_store.py

```python
"""FAISS vector store management — local development."""
from backend.rag.pipeline import ingest_documents
from backend.rag.retriever import RAGRetriever

def build_index():
    """Run full ingestion pipeline."""
    ingest_documents()

def get_retriever() -> RAGRetriever:
    """Get singleton retriever (loads index from disk)."""
    return RAGRetriever()
```

---

## RAG Evaluation Metrics

Run these checks after ingestion to verify quality:

| Test | Command | Expected |
|------|---------|---------|
| Chunk count | `python -c "import pickle; d=pickle.load(open('vectorstore/faiss_index/metadata.pkl','rb')); print(len(d))"` | > 100 chunks |
| FAISS index size | `python -c "import faiss; i=faiss.read_index('vectorstore/faiss_index/index.faiss'); print(i.ntotal)"` | Matches chunk count |
| Sample retrieval | `python -c "from backend.rag.retriever import retriever; print(retriever.search('refund policy'))"` | Returns relevant chunks |

---

## Updating the Knowledge Base

When a new PDF is uploaded via `/admin/upload`:

1. Save PDF to `knowledge_base/`
2. Call `ingest_documents()` — this rebuilds the full index
3. Reload `RAGRetriever` singleton (restart instance or call `_load_index()`)

For production with Pinecone, use namespace-based upsert to avoid full re-index.
