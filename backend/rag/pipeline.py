"""
Offline RAG ingestion pipeline (the "Kaggle Factory" heavy-lifting step).

This builds the FAISS index from the knowledge_base PDFs. It is a DEVELOPMENT /
OFFLINE tool — in production we load the pre-built artifact instead of rebuilding
it (see documentations/13_KAGGLE_FACTORY_PATTERN.md). Running it on a live
production server is slow, costly, and — on Apple Silicon — can segfault on
interpreter shutdown during PyTorch/MPS cleanup.

Guards:
- Embedding runs on CPU (settings.EMBEDDING_DEVICE) to avoid the MPS segfault.
- Ingestion refuses to run in production unless ENABLE_INGESTION=true.
"""
import pickle
from pathlib import Path

import faiss
import numpy as np
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.embeddings.encoder import EmbeddingEncoder
from backend.config import settings

KNOWLEDGE_BASE_DIR = Path("knowledge_base")
INDEX_DIR = Path("vectorstore/faiss_index")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def _ingestion_allowed() -> bool:
    """Block ingestion in production unless explicitly enabled."""
    if settings.ENVIRONMENT == "production" and not settings.ENABLE_INGESTION:
        print(
            "Ingestion is disabled in production. Load the pre-built Kaggle "
            "artifact into vectorstore/faiss_index/ (or use Pinecone). "
            "Set ENABLE_INGESTION=true to override."
        )
        return False
    return True


def ingest_documents():
    """Load all PDFs, chunk, embed, and build/persist the FAISS index."""
    if not _ingestion_allowed():
        return

    encoder = EmbeddingEncoder()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    all_chunks = []
    all_metadata = []

    pdf_files = list(KNOWLEDGE_BASE_DIR.glob("*.pdf"))
    if not pdf_files:
        print("No PDFs found in knowledge_base/. Add PDFs and re-run.")
        return

    for pdf_path in pdf_files:
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

    if not all_chunks:
        print("No text extracted from PDFs.")
        return

    print(f"Total chunks: {len(all_chunks)}")

    # Offline heavy-lift: progress bar is helpful here (unlike the request path).
    embeddings = encoder.encode(all_chunks, show_progress_bar=True)
    embeddings_np = np.array(embeddings).astype("float32")

    dimension = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_np)

    # Persist the artifact so the retriever can load it. Previously this only
    # ran in production — the exact environment where the pattern says NOT to
    # rebuild — leaving dev with no on-disk index.
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_DIR / "index.faiss"))
    with open(INDEX_DIR / "metadata.pkl", "wb") as f:
        pickle.dump(all_metadata, f)
    print(f"Index saved to {INDEX_DIR} ({index.ntotal} vectors)")


if __name__ == "__main__":
    ingest_documents()
