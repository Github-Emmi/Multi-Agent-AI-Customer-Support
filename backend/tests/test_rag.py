"""
Unit Tests — RAG Pipeline & Retriever
V-Model Phase: Unit Testing
Tests: ingestion, chunking, embedding, FAISS index, semantic retrieval
"""
import os
import pytest
import tempfile
import pickle
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestEmbeddingEncoder:
    def test_encode_returns_list_of_floats(self):
        from backend.embeddings.encoder import EmbeddingEncoder
        encoder = EmbeddingEncoder()
        vectors = encoder.encode(["Hello world", "TechMart refund policy"])
        assert len(vectors) == 2
        assert isinstance(vectors[0], list)
        assert all(isinstance(x, float) for x in vectors[0])

    def test_encode_query_returns_single_vector(self):
        from backend.embeddings.encoder import EmbeddingEncoder
        encoder = EmbeddingEncoder()
        vec = encoder.encode_query("What is the refund policy?")
        assert isinstance(vec, list)
        assert len(vec) == 384  # all-MiniLM-L6-v2 dimension

    def test_singleton_behavior(self):
        from backend.embeddings.encoder import EmbeddingEncoder
        e1 = EmbeddingEncoder()
        e2 = EmbeddingEncoder()
        assert e1 is e2


class TestRAGPipeline:
    def test_ingest_with_no_pdfs_does_not_crash(self):
        """Should warn and return cleanly when knowledge_base/ is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("backend.rag.pipeline.KNOWLEDGE_BASE_DIR", Path(tmpdir)), \
                 patch("backend.rag.pipeline.INDEX_DIR", Path(tmpdir) / "index"):
                from backend.rag.pipeline import ingest_documents
                # Should not raise
                ingest_documents()

    def test_ingest_creates_faiss_index(self):
        """Create a minimal text-based test to verify index creation."""
        import faiss
        import numpy as np

        with tempfile.TemporaryDirectory() as tmpdir:
            kb_dir = Path(tmpdir) / "kb"
            idx_dir = Path(tmpdir) / "idx"
            kb_dir.mkdir()

            # Create a fake PDF using fpdf2 if available, else skip
            try:
                from fpdf import FPDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Helvetica", size=12)
                pdf.cell(0, 10, "TechMart refund policy: 30 days money back guarantee.", ln=True)
                pdf.output(str(kb_dir / "test.pdf"))
            except ImportError:
                pytest.skip("fpdf2 not installed — skipping PDF ingestion test")

            with patch("backend.rag.pipeline.KNOWLEDGE_BASE_DIR", kb_dir), \
                 patch("backend.rag.pipeline.INDEX_DIR", idx_dir):
                from backend.rag import pipeline as p
                import importlib
                importlib.reload(p)
                p.KNOWLEDGE_BASE_DIR = kb_dir
                p.INDEX_DIR = idx_dir
                p.ingest_documents()

                assert (idx_dir / "index.faiss").exists()
                assert (idx_dir / "metadata.pkl").exists()

                index = faiss.read_index(str(idx_dir / "index.faiss"))
                assert index.ntotal > 0


class TestRAGRetriever:
    def test_retriever_returns_empty_when_no_index(self):
        from backend.rag.retriever import RAGRetriever
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("backend.rag.retriever.INDEX_DIR", Path(tmpdir)):
                # Bypass singleton
                r = object.__new__(RAGRetriever)
                r._load_index()
                results = r.search("refund policy", top_k=4)
                assert results == []

    def test_retriever_search_returns_scored_chunks(self):
        """Build a tiny real FAISS index and verify search works."""
        import faiss
        import numpy as np

        with tempfile.TemporaryDirectory() as tmpdir:
            idx_dir = Path(tmpdir)
            chunks = [
                {"text": "Refund within 30 days.", "source": "refund_policy.pdf",
                 "page": 1, "chunk_id": "r_0"},
                {"text": "Password reset via email.", "source": "user_manual.pdf",
                 "page": 1, "chunk_id": "u_0"},
            ]
            from backend.embeddings.encoder import EmbeddingEncoder
            encoder = EmbeddingEncoder()
            vecs = np.array(encoder.encode([c["text"] for c in chunks])).astype("float32")
            index = faiss.IndexFlatL2(vecs.shape[1])
            index.add(vecs)
            faiss.write_index(index, str(idx_dir / "index.faiss"))
            with open(idx_dir / "metadata.pkl", "wb") as f:
                pickle.dump(chunks, f)

            from backend.rag.retriever import RAGRetriever
            r = object.__new__(RAGRetriever)
            with patch("backend.rag.retriever.INDEX_DIR", idx_dir):
                r._load_index()

            results = r.search("I want a refund", top_k=2)
            assert len(results) > 0
            assert "text" in results[0]
            assert "score" in results[0]
            # Top result should be refund-related
            assert "refund" in results[0]["text"].lower()


class TestRetrievalPrecision:
    """
    RAG Evaluation — Acceptance criterion: precision >= 80%
    V-Model Phase: Acceptance Testing
    """

    PRECISION_TESTS = [
        ("How do I get a refund?", "refund_policy"),
        ("How do I reset my password?", "user_manual"),
        ("What is the warranty on laptops?", "warranty"),
        ("What are your business hours?", "faq"),
        ("How long does delivery take?", "shipping_policy"),
    ]

    @pytest.mark.skipif(
        not Path("vectorstore/faiss_index/index.faiss").exists(),
        reason="FAISS index not built — run python -m backend.rag.pipeline first",
    )
    def test_retrieval_precision_80_percent(self):
        from backend.rag.retriever import retriever

        passed = 0
        failures = []
        for query, expected_source in self.PRECISION_TESTS:
            results = retriever.search(query, top_k=4)
            sources = [r.get("source", "").lower() for r in results]
            hit = any(expected_source in s for s in sources)
            if hit:
                passed += 1
            else:
                failures.append(f"FAIL: '{query}' — expected '{expected_source}', got {sources}")

        precision = passed / len(self.PRECISION_TESTS)
        assert precision >= 0.80, (
            f"Retrieval precision {precision:.0%} is below 80% target.\n"
            + "\n".join(failures)
        )
