"""Technical Support Agent — handles login, password reset, installation, errors, bugs."""
from backend.rag.retriever import retriever
from backend.config import settings
from langchain_openai import ChatOpenAI

SYSTEM_PROMPT = """You are the Technical Support Specialist for TechMart Electronics.
You handle: login issues, password resets, installation problems, errors, and bugs.
Only answer technical support questions. For other topics, say
"Let me connect you with the right specialist for that."

For password resets, remind the customer to check their spam/junk folder if the
reset email doesn't arrive within 5 minutes.

Use ONLY the context below. Do not invent information.

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


def technical_node(state: dict) -> dict:
    query = state["query"]
    history = _format_history(state.get("conversation_history", []))

    chunks = retriever.search(query, top_k=4)
    context = "\n\n".join([c["text"] for c in chunks]) or "No relevant documents found."
    state["retrieved_contexts"]["technical"] = chunks

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
    state["agent_responses"].append({"agent": "technical", "response": response})
    return state
