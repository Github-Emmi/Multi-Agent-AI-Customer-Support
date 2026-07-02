"""Technical Support Agent — handles login, password reset, installation, errors, bugs."""
from backend.rag.retriever import retriever
from backend.config import settings
from backend.agents.utils import format_history
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


def technical_node(state: dict) -> dict:
    query = state["query"]
    history = format_history(state.get("conversation_history", []))

    chunks = retriever.search(query, top_k=4)
    context = "\n\n".join([c["text"] for c in chunks]) or "No relevant documents found."
    state["retrieved_contexts"]["technical"] = chunks

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
    state["agent_responses"].append({"agent": "technical", "response": response})
    return state
