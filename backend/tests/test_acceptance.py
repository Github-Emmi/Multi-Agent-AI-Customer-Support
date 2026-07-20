"""
Acceptance Tests — System-level quality gates
V-Model Phase: Acceptance Testing
Tests: end-to-end quality metrics against business requirements.
These tests may require real services (LLMs) and a built index.
"""
import pytest
import asyncio
from unittest.mock import patch

# Acceptance Criteria: Intent classification accuracy >= 85%
INTENT_ACCURACY_TESTS = [
    ("I need a refund for my last order.", ["billing"]),
    ("My subscription won't activate.", ["billing", "technical"]),
    ("How do I reset my password?", ["technical"]),
    ("The website is not loading.", ["technical"]),
    ("What is the warranty on the new UltraBook?", ["product"]),
    ("Do you have any student discounts?", ["product", "billing"]),
    ("I'm very unhappy with the service I received.", ["complaint"]),
    ("This is unacceptable, I want to speak to a manager.", ["complaint"]),
    ("What are your business hours?", ["faq"]),
    ("Where is your company located?", ["faq"]),
    # Add more test cases to have a representative sample
    ("My payment failed.", ["billing"]),
    ("The screen on my new phone is cracked.", ["product", "complaint"]),
]

@pytest.mark.asyncio
@pytest.mark.acceptance
@pytest.mark.skipif(
    "not os.environ.get('OPENROUTER_API_KEY')",
    reason="Acceptance test requires OPENROUTER_API_KEY to be set."
)
class TestIntentAccuracy:
    
    async def test_intent_classification_accuracy(self):
        from backend.agents.router import detect_intent

        passed = 0
        failures = []

        # We need to create a basic state for the function to run
        def _make_state(query: str) -> dict:
            return {
                "query": query, "session_id": "test", "conversation_history": [],
                "intents": [], "sentiment_score": 1, "retrieved_contexts": {},
                "agent_responses": [], "final_response": "", "agents_used": [],
                "response_time_ms": 0,
            }

        for query, expected_intents in INTENT_ACCURACY_TESTS:
            # We don't want sentiment analysis to interfere with this test
            with patch("backend.agents.router.get_sentiment", return_value=1):
                 # The detect_intent function is not async, so we can call it directly
                state = _make_state(query)
                # detect_intent is not async, it uses an async function inside.
                # To test it we would need to run it in an event loop.
                # However, for this acceptance test, we assume the outer test runner handles the loop.
                # Let's check the source again. `detect_intent` itself is not async.
                # But it calls an LLM, which might be. Let's assume it works in this context.
                # After re-reading test_agents, I see it's not an async function.
                
                # Let's make this an async loop to be safe
                loop = asyncio.get_event_loop()
                result_state = await loop.run_in_executor(None, lambda: detect_intent(state))
                
                # Sort both lists to ensure comparison is order-independent
                predicted_intents = sorted(result_state.get("intents", []))
                expected_intents = sorted(expected_intents)

                if predicted_intents == expected_intents:
                    passed += 1
                else:
                    failures.append(f"FAIL: '{query}' -> Expected {expected_intents}, Got {predicted_intents}")
            
            # Add a small delay to avoid hitting API rate limits
            await asyncio.sleep(1)

        accuracy = passed / len(INTENT_ACCURACY_TESTS)
        print(f"Intent Classification Accuracy: {accuracy:.2%}")
        
        assert accuracy >= 0.85, (
            f"Intent classification accuracy {accuracy:.2%} is below 85% target.
"
            + "
".join(failures)
        )
