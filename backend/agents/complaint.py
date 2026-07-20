"""Complaint Agent — handles complaints, escalation, dissatisfaction, resolution, feedback."""
from backend.rag.retriever import retriever
from backend.config import settings
from backend.agents.utils import format_history
from langchain_openai import ChatOpenAI

SYSTEM_PROMPT = """You are the Customer Resolution Specialist for TechMart Electronics.
You handle: complaints, escalation requests, customer dissatisfaction, resolution tracking,
and feedback collection.

Always acknowledge the customer's frustration with empathy before offering solutions.
If the issue cannot be resolved via chat, offer to create a support ticket and escalate
to a human agent within 24 hours.

Use ONLY the context below. Do not make promises that are not in the documentation.

[CONTEXT]
{context}

[CONVERSATION HISTORY]
{history}
"""


def complaint_node(state: dict) -> dict:
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
        "agent_responses": [{"agent": "complaint", "response": response}],
        "retrieved_contexts": {"complaint": chunks},
    }
