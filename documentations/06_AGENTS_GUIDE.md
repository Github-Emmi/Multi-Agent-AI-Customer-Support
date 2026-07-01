# 06 — Multi-Agent System Design

> **Project:** Multi-Agent AI Customer Support Assistant  
> **Orchestration:** LangGraph  
> **LLM Gateway:** openrouter.ai

---

## Agent System Overview

```
User Query
    │
    ▼
┌──────────────────────────┐
│   Intent Detection Agent  │
│   Classify into domains   │
│   Output: ["billing",     │
│            "technical"]   │
└──────────────┬────────────┘
               │
               ▼
┌──────────────────────────┐
│      Agent Router         │
│   LangGraph conditional   │
│   edges → parallel nodes  │
└──┬──────┬───────┬──────┬──┘
   │      │       │      │
   ▼      ▼       ▼      ▼
Billing Tech  Product Complaint  FAQ
Agent   Agent  Agent   Agent    Agent
   │      │       │      │       │
   └──────┴───────┴──────┴───────┘
                  │
                  ▼
        Response Aggregator
                  │
                  ▼
           Final Response
```

---

## LangGraph State Schema

```python
from typing import TypedDict, List, Optional, Annotated
import operator

class AgentState(TypedDict):
    # Input
    query: str
    session_id: str
    conversation_history: List[dict]

    # Routing
    intents: List[str]           # ["billing", "technical"]

    # RAG
    retrieved_contexts: dict     # {agent_name: [chunks]}

    # Responses
    agent_responses: Annotated[List[dict], operator.add]
    # [{agent: "billing", response: "...", confidence: 0.9}]

    # Output
    final_response: Optional[str]
    agents_used: List[str]
    response_time_ms: Optional[int]
```

---

## Intent Detection Agent

**File:** `backend/agents/router.py`

```python
INTENT_LABELS = ["billing", "technical", "product", "complaint", "faq"]

INTENT_PROMPT = """
You are an intent classifier for a customer support system.
Analyze the customer query and return a JSON array of one or more
intents from this list: {labels}

Query: {query}

Return ONLY a JSON array, e.g. ["billing"] or ["billing", "technical"]
"""

def detect_intent(state: AgentState) -> AgentState:
    prompt = INTENT_PROMPT.format(
        labels=INTENT_LABELS,
        query=state["query"]
    )
    response = llm_client.complete(prompt)
    intents = json.loads(response)
    state["intents"] = intents
    return state
```

---

## Agent Router — LangGraph Graph

```python
from langgraph.graph import StateGraph, END

def build_agent_graph():
    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("intent_detection", detect_intent)
    graph.add_node("billing_agent", billing_node)
    graph.add_node("technical_agent", technical_node)
    graph.add_node("product_agent", product_node)
    graph.add_node("complaint_agent", complaint_node)
    graph.add_node("faq_agent", faq_node)
    graph.add_node("aggregator", aggregate_responses)

    # Entry
    graph.set_entry_point("intent_detection")

    # Conditional routing
    graph.add_conditional_edges(
        "intent_detection",
        route_to_agents,          # returns list of next nodes
        {
            "billing": "billing_agent",
            "technical": "technical_agent",
            "product": "product_agent",
            "complaint": "complaint_agent",
            "faq": "faq_agent",
        }
    )

    # All agents → aggregator
    for agent in ["billing_agent", "technical_agent", "product_agent",
                  "complaint_agent", "faq_agent"]:
        graph.add_edge(agent, "aggregator")

    graph.add_edge("aggregator", END)

    return graph.compile()
```

---

## Specialized Agent Template

Each agent follows the same structure:

```python
# backend/agents/billing.py

BILLING_SYSTEM_PROMPT = """
You are the Billing Specialist for TechMart Electronics.
You handle: payment issues, subscriptions, invoices, and refunds.
Only answer billing-related questions.
If asked about other topics, say: "Let me connect you with the right specialist."

Use ONLY the information from the context below to answer.
Do not make up information.

[CONTEXT]
{context}

[CONVERSATION HISTORY]
{history}
"""

def billing_node(state: AgentState) -> AgentState:
    query = state["query"]
    history = format_history(state["conversation_history"])

    # RAG retrieval
    chunks = retriever.search(query, namespace="billing", top_k=4)
    context = "\n\n".join([c["text"] for c in chunks])

    # Store retrieved context
    state["retrieved_contexts"]["billing"] = chunks

    # Build prompt
    messages = [
        {"role": "system", "content": BILLING_SYSTEM_PROMPT.format(
            context=context, history=history)},
        {"role": "user", "content": query}
    ]

    # LLM call
    response = llm_client.chat(messages)

    # Append to state
    state["agent_responses"].append({
        "agent": "billing",
        "response": response,
    })
    return state
```

---

## Agent Domain Scopes

### Billing Agent (`billing.py`)

| Handles | Knowledge Sources |
|---------|-----------------|
| Payment issues | `refund_policy.pdf`, `pricing.pdf` |
| Subscription management | `pricing.pdf`, `faq.pdf` |
| Invoice queries | `refund_policy.pdf` |
| Refund requests | `refund_policy.pdf` |

### Technical Support Agent (`technical.py`)

| Handles | Knowledge Sources |
|---------|-----------------|
| Login problems | `user_manual.pdf`, `faq.pdf` |
| Password reset | `user_manual.pdf` |
| Installation issues | `installation_guide.pdf` |
| Errors and bugs | `user_manual.pdf` |

### Product Agent (`product.py`)

| Handles | Knowledge Sources |
|---------|-----------------|
| Product features | `products.pdf`, `user_manual.pdf` |
| Pricing | `pricing.pdf` |
| Product comparisons | `products.pdf` |
| Availability | `products.pdf` |
| Warranty | `warranty.pdf` |

### Complaint Agent (`complaint.py`)

| Handles | Knowledge Sources |
|---------|-----------------|
| Complaint recording | `faq.pdf` |
| Escalation | `faq.pdf` |
| Customer dissatisfaction | `refund_policy.pdf` |
| Resolution tracking | `faq.pdf` |
| Feedback collection | — |

### FAQ Agent (`faq.py`)

| Handles | Knowledge Sources |
|---------|-----------------|
| Company policies | `faq.pdf`, `shipping_policy.pdf` |
| General questions | `faq.pdf` |
| Contact information | `faq.pdf` |

---

## Response Aggregator

```python
def aggregate_responses(state: AgentState) -> AgentState:
    responses = state["agent_responses"]

    if len(responses) == 1:
        # Single agent — return directly
        state["final_response"] = responses[0]["response"]
    else:
        # Multi-agent — merge with section headers
        parts = []
        for r in responses:
            parts.append(f"**{r['agent'].title()} Team:**\n{r['response']}")
        state["final_response"] = "\n\n".join(parts)

    state["agents_used"] = [r["agent"] for r in responses]
    return state
```

---

## Sentiment Analysis Integration

Before routing, detect frustration level:

```python
SENTIMENT_PROMPT = """
Rate the frustration level of this customer message on a scale of 1-5.
1 = calm, 5 = very frustrated/angry
Return ONLY the number.

Message: {query}
"""

def sentiment_check(state: AgentState) -> AgentState:
    score = int(llm_client.complete(
        SENTIMENT_PROMPT.format(query=state["query"])
    ).strip())

    if score >= 4:
        # High frustration — ensure complaint agent is included
        if "complaint" not in state["intents"]:
            state["intents"].append("complaint")

    state["sentiment_score"] = score
    return state
```
