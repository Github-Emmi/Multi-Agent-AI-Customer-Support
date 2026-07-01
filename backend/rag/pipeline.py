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

    embeddings = encoder.encode(all_chunks)
    embeddings_np = np.array(embeddings).astype("float32")

    dimension = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_np)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_DIR / "index.faiss"))
    with open(INDEX_DIR / "metadata.pkl", "wb") as f:
        pickle.dump(all_metadata, f)

    print(f"Index saved to {INDEX_DIR} ({index.ntotal} vectors)")


if __name__ == "__main__":
    ingest_documents()
