"""
Integration Tests — Full Agent Orchestration
V-Model Phase: Integration Testing
Tests: full flow from API → intent → route → RAG → LLM (mocked)
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import faiss
import numpy as np
import pickle
from pathlib import Path
import tempfile

# This setup is similar to test_rag.py to create a real, temporary FAISS index
@pytest_asyncio.fixture(scope="module")
async def temp_faiss_index():
    with tempfile.TemporaryDirectory() as tmpdir:
        idx_dir = Path(tmpdir)
        
        # Define some chunks that correspond to different agent domains
        chunks = [
            {"text": "Our refund policy allows for returns within 30 days.", "source": "billing_docs.pdf", "page": 1, "chunk_id": "b_0"},
            {"text": "You can reset your password by clicking 'Forgot Password'.", "source": "tech_docs.pdf", "page": 1, "chunk_id": "t_0"},
            {"text": "The UltraBook Pro has a 16-inch screen.", "source": "product_docs.pdf", "page": 2, "chunk_id": "p_0"},
        ]

        # Use the actual encoder to create embeddings
        from backend.embeddings.encoder import EmbeddingEncoder
        encoder = EmbeddingEncoder()
        vecs = np.array(encoder.encode([c["text"] for c in chunks])).astype("float32")
        
        # Create and save a FAISS index
        index = faiss.IndexFlatL2(vecs.shape[1])
        index.add(vecs)
        faiss.write_index(index, str(idx_dir / "index.faiss"))
        
        # Save metadata
        with open(idx_dir / "metadata.pkl", "wb") as f:
            pickle.dump(chunks, f)
        
        yield idx_dir

# Mock the LLM calls for the entire module
@pytest.fixture(scope="module", autouse=True)
def mock_llms():
    # This mock will handle both intent detection and agent response generation
    mock_llm_instance = MagicMock()
    
    def invoke_side_effect(prompt):
        resp = MagicMock()
        prompt_str = str(prompt)
        if "intent classifier" in prompt_str:
            if "refund" in prompt_str:
                resp.content = '["billing"]'
            elif "password" in prompt_str:
                resp.content = '["technical"]'
            else:
                resp.content = '["faq"]'
        elif "Billing Specialist" in prompt_str:
            resp.content = "Billing response based on context."
        elif "Technical Support" in prompt_str:
            resp.content = "Technical response based on context."
        else:
            resp.content = "Generic fallback response."
        return resp

    mock_llm_instance.invoke.side_effect = invoke_side_effect

    with patch("backend.agents.router.get_llm", return_value=mock_llm_instance), 
         patch("backend.agents.billing.get_llm", return_value=mock_llm_instance), 
         patch("backend.agents.technical.get_llm", return_value=mock_llm_instance), 
         patch("backend.agents.product.get_llm", return_value=mock_llm_instance), 
         patch("backend.agents.complaint.get_llm", return_value=mock_llm_instance), 
         patch("backend.agents.faq.get_llm", return_value=mock_llm_instance):
        yield

@pytest.mark.asyncio
@pytest.mark.integration
class TestAgentIntegration:
    async def test_billing_query_full_flow(self, client, auth_headers, temp_faiss_index):
        # The retriever will use the temporary index we created
        with patch("backend.rag.retriever.INDEX_DIR", temp_faiss_index):
            # We need to reload the retriever singleton to use the new index path
            from backend.rag.retriever import retriever
            retriever._load_index()

            resp = await client.post(
                "/chat",
                json={"session_id": "sess_integration_001", "message": "I want a refund"},
                headers=auth_headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        
        # Check that the correct agent was used (based on our mock LLM's intent detection)
        assert data["agents_used"] == ["billing"]
        
        # Check that the final response is from the billing agent (based on our mock agent response)
        assert data["response"] == "Billing response based on context."

    async def test_technical_query_full_flow(self, client, auth_headers, temp_faiss_index):
        with patch("backend.rag.retriever.INDEX_DIR", temp_faiss_index):
            from backend.rag.retriever import retriever
            retriever._load_index()

            resp = await client.post(
                "/chat",
                json={"session_id": "sess_integration_002", "message": "forgot my password"},
                headers=auth_headers,
            )
            
        assert resp.status_code == 200
        data = resp.json()
        assert data["agents_used"] == ["technical"]
        assert data["response"] == "Technical response based on context."

