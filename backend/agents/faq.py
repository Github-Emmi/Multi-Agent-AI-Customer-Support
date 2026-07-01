"""FAQ Agent — handles company policies, general questions, contact information."""
from backend.rag.retriever import retriever
from backend.config import settings
from backend.agents.utils import format_history
from langchain_openai import ChatOpenAI

SYSTEM_PROMPT = """You are the General Support Specialist for TechMart Electronics.
You handle: company policies, general questions, and contact information.
If a question belongs to a more specific domain (billing, technical, product, or complaints),
say "Let me connect you with the right specialist for that."

Use ONLY the context below. Do not invent policies or contact details.

[CONTEXT]
{context}

[CONVERSATION HISTORY]
{history}
"""


def faq_node(state: dict) -> dict:
    query = state["query"]
    history = format_history(state.get("conversation_history", []))

    chunks = retriever.search(query, top_k=4)
    context = "\n\n".join([c["text"] for c in chunks]) or "No relevant documents found."
    state["retrieved_contexts"]["faq"] = chunks

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
    state["agent_responses"].append({"agent": "faq", "response": response})
    return state
