"""
Agent Router — LangGraph Orchestrator
Detects intent, sentiment, and language; dispatches to specialized agents.
"""
import json
import logging
import time
from typing import List, Annotated, Optional
import operator
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from backend.config import settings
from backend.agents.billing import billing_node
from backend.agents.technical import technical_node
from backend.agents.product import product_node
from backend.agents.complaint import complaint_node
from backend.agents.faq import faq_node

logger = logging.getLogger("techmart.router")

INTENT_LABELS = ["billing", "technical", "product", "complaint", "faq"]

INTENT_PROMPT = """You are an intent classifier for TechMart Electronics customer support.
Analyze the customer message and return a JSON array of one or more intents.
Choose only from: {labels}

Customer message: {query}

Return ONLY a valid JSON array, e.g. ["billing"] or ["billing", "technical"]"""

SENTIMENT_PROMPT = """Rate the frustration level of this customer message on a scale 1-5.
1=calm, 5=very frustrated. Return ONLY the number.

Message: {query}"""


class AgentState(TypedDict):
    query: str
    session_id: str
    conversation_history: List[dict]
    intents: List[str]
    sentiment_score: int
    sentiment_label: str
    language_code: str
    language_instruction: str
    retrieved_contexts: dict
    agent_responses: Annotated[List[dict], operator.add]
    final_response: str
    agents_used: List[str]
    response_time_ms: int


def get_llm():
    return ChatOpenAI(
        base_url=settings.OPENAI_BASE_URL,
        api_key=settings.OPENROUTER_API_KEY,
        model=settings.OPENAI_MODEL,
        temperature=settings.OPENAI_TEMPERATURE,
        max_tokens=settings.OPENAI_MAX_TOKENS,
    )


def detect_intent(state: AgentState) -> AgentState:
    llm = get_llm()
    prompt = INTENT_PROMPT.format(
        labels=INTENT_LABELS,
        query=state["query"],
    )
    response = llm.invoke(prompt).content.strip()
    try:
        intents = json.loads(response)
        intents = [i for i in intents if i in INTENT_LABELS]
    except (json.JSONDecodeError, TypeError):
        intents = ["faq"]
    state["intents"] = intents if intents else ["faq"]

    # Sentiment check — add complaint agent for high frustration
    sentiment_resp = llm.invoke(
        SENTIMENT_PROMPT.format(query=state["query"])
    ).content.strip()
    try:
        score = int(sentiment_resp[0])
    except (ValueError, IndexError):
        score = 2
    state["sentiment_score"] = score
    if score >= 4 and "complaint" not in state["intents"]:
        state["intents"].append("complaint")

    state["retrieved_contexts"] = {}
    state["agent_responses"] = []
    return state


def route_to_agents(state: AgentState) -> List[str]:
    return state["intents"]


def aggregate_responses(state: AgentState) -> AgentState:
    responses = state["agent_responses"]
    if not responses:
        state["final_response"] = (
            "I'm sorry, I wasn't able to process your request. "
            "Please try again or contact our support team."
        )
        state["agents_used"] = []
        return state

    if len(responses) == 1:
        state["final_response"] = responses[0]["response"]
    else:
        parts = []
        for r in responses:
            parts.append(f"**{r['agent'].title()} Team:**\n{r['response']}")
        state["final_response"] = "\n\n".join(parts)

    state["agents_used"] = [r["agent"] for r in responses]
    return state


def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("intent_detection", detect_intent)
    graph.add_node("billing_agent", billing_node)
    graph.add_node("technical_agent", technical_node)
    graph.add_node("product_agent", product_node)
    graph.add_node("complaint_agent", complaint_node)
    graph.add_node("faq_agent", faq_node)
    graph.add_node("aggregator", aggregate_responses)

    graph.set_entry_point("intent_detection")

    graph.add_conditional_edges(
        "intent_detection",
        route_to_agents,
        {
            "billing": "billing_agent",
            "technical": "technical_agent",
            "product": "product_agent",
            "complaint": "complaint_agent",
            "faq": "faq_agent",
        },
    )

    for agent_node in [
        "billing_agent", "technical_agent", "product_agent",
        "complaint_agent", "faq_agent",
    ]:
        graph.add_edge(agent_node, "aggregator")

    graph.add_edge("aggregator", END)
    return graph.compile()


agent_graph = build_agent_graph()


async def run_agents(
    query: str,
    session_id: str,
    conversation_history: List[dict],
) -> dict:
    start = time.time()
    state = AgentState(
        query=query,
        session_id=session_id,
        conversation_history=conversation_history,
        intents=[],
        sentiment_score=1,
        sentiment_label="neutral",
        language_code="en",
        language_instruction="",
        retrieved_contexts={},
        agent_responses=[],
        final_response="",
        agents_used=[],
        response_time_ms=0,
    )
    result = await agent_graph.ainvoke(state)
    result["response_time_ms"] = int((time.time() - start) * 1000)
    logger.info(
        f"[{session_id}] agents={result.get('agents_used')} "
        f"sentiment={result.get('sentiment_score')} "
        f"lang={result.get('language_code')} "
        f"time={result['response_time_ms']}ms"
    )
    return result
