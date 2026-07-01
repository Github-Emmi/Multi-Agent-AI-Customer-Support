"""Product Agent — handles features, pricing, comparisons, availability, warranty."""
from backend.rag.retriever import retriever
from backend.config import settings
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


def _format_history(history):
    lines = []
    for turn in history[-5:]:
        role = "Customer" if turn["role"] == "user" else "Assistant"
        lines.append(f"{role}: {turn['content']}")
    return "\n".join(lines) if lines else "No previous conversation."


def product_node(state: dict) -> dict:
    query = state["query"]
    history = _format_history(state.get("conversation_history", []))

    chunks = retriever.search(query, top_k=4)
    context = "\n\n".join([c["text"] for c in chunks]) or "No relevant documents found."
    state["retrieved_contexts"]["product"] = chunks

    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
        model="meta-llama/llama-3-8b-instruct:free",
        temperature=0.2,
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(context=context, history=history)},
        {"role": "user", "content": query},
    ]
    response = llm.invoke(messages).content.strip()
    state["agent_responses"].append({"agent": "product", "response": response})
    return state
