"""Product Agent — handles features, pricing, comparisons, availability, warranty."""
from backend.rag.retriever import retriever
from backend.config import settings
from backend.agents.utils import format_history
from langchain_openai import ChatOpenAI

SYSTEM_PROMPT = """You are the Product Specialist for TechMart Electronics.
You handle: product features, pricing, comparisons, availability, and warranty information.
Only answer product-related questions. For other topics, say
"Let me connect you with the right specialist for that."

Use ONLY the context below. Do not invent product specifications or prices.

[CONTEXT]
{context}

[CONVERSATION HISTORY]
{history}
"""


def product_node(state: dict) -> dict:
    query = state["query"]
    history = format_history(state.get("conversation_history", []))

    chunks = retriever.search(query, top_k=4)
    context = "\n\n".join([c["text"] for c in chunks]) or "No relevant documents found."

    llm = ChatOpenAI(
        base_url=settings.OPENAI_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY,
        model=settings.OPENAI_MODEL,
        temperature=settings.OPENAI_TEMPERATURE,
        max_tokens=settings.OPENAI_MAX_TOKENS,
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(context=context, history=history)},
        {"role": "user", "content": query},
    ]
    response = llm.invoke(messages).content.strip()
    return {
        "agent_responses": [{"agent": "product", "response": response}],
        "retrieved_contexts": {"product": chunks},
    }
