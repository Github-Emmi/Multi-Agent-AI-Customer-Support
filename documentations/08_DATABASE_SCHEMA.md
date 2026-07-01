# 08 — Database Schema

> **Project:** Multi-Agent AI Customer Support Assistant  
> **Database:** MongoDB Atlas  
> **Collections:** users, sessions, conversations, analytics, tickets

---

## Collections Overview

| Collection | Purpose |
|------------|---------|
| `users` | Registered user accounts |
| `sessions` | Active chat sessions |
| `conversations` | Full message history per session |
| `analytics` | Aggregated metrics per conversation |
| `tickets` | Auto-created support tickets |
| `kb_documents` | Knowledge base document registry |

---

## Collection: `users`

```json
{
  "_id": "ObjectId",
  "name": "Jane Smith",
  "email": "jane@example.com",
  "password_hash": "$2b$12$...",          // bcrypt hash
  "role": "user",                          // "user" | "admin"
  "created_at": "2026-07-01T10:00:00Z",
  "last_login": "2026-07-01T14:00:00Z",
  "is_active": true,
  "reset_token": null,                     // password reset token (temporary)
  "reset_token_expiry": null
}
```

**Indexes:**
- `email` — unique
- `reset_token` — sparse

---

## Collection: `sessions`

```json
{
  "_id": "ObjectId",
  "session_id": "sess_abc123",             // UUID
  "user_id": "ObjectId → users",
  "title": "Payment not processed",        // auto-generated from first message
  "created_at": "2026-07-01T10:00:00Z",
  "updated_at": "2026-07-01T10:05:00Z",
  "is_resolved": false,
  "ticket_id": null                        // linked ticket if escalated
}
```

**Indexes:**
- `user_id`
- `session_id` — unique
- `updated_at` (descending, for recent sessions query)

---

## Collection: `conversations`

```json
{
  "_id": "ObjectId",
  "session_id": "sess_abc123",
  "turns": [
    {
      "turn_id": 1,
      "role": "user",
      "content": "I paid yesterday but Premium is still locked.",
      "timestamp": "2026-07-01T10:00:01Z"
    },
    {
      "turn_id": 2,
      "role": "assistant",
      "content": "I understand your frustration...",
      "timestamp": "2026-07-01T10:00:04Z",
      "agents_used": ["billing", "technical"],
      "response_time_ms": 2840,
      "retrieved_chunks": [
        {
          "source": "refund_policy.pdf",
          "page": 2,
          "score": 0.12
        }
      ]
    }
  ]
}
```

**Indexes:**
- `session_id` — unique (one document per session)

---

## Collection: `analytics`

```json
{
  "_id": "ObjectId",
  "session_id": "sess_abc123",
  "user_id": "ObjectId → users",
  "date": "2026-07-01",
  "total_turns": 6,
  "agents_used": ["billing", "technical"],
  "avg_response_time_ms": 2650,
  "satisfaction_rating": 4,               // 1-5, null if not rated
  "satisfaction_comment": "Very helpful!",
  "was_escalated": false,
  "ticket_created": false,
  "sentiment_scores": [2, 3, 2],          // frustration level per user turn
  "resolved": true
}
```

**Indexes:**
- `date` (for daily aggregations)
- `user_id`
- `agents_used` (multikey)

---

## Collection: `tickets`

```json
{
  "_id": "ObjectId",
  "ticket_id": "TKT-20260701-0042",       // human-readable ID
  "session_id": "sess_abc123",
  "user_id": "ObjectId → users",
  "subject": "Payment processed but Premium locked",
  "description": "Auto-generated summary of conversation...",
  "status": "open",                        // "open" | "in_progress" | "resolved" | "closed"
  "priority": "high",                      // "low" | "medium" | "high" | "urgent"
  "assigned_agent": null,                  // human agent email if handed off
  "created_at": "2026-07-01T10:05:00Z",
  "updated_at": "2026-07-01T10:05:00Z",
  "resolved_at": null
}
```

**Indexes:**
- `ticket_id` — unique
- `status`
- `user_id`

---

## Collection: `kb_documents`

```json
{
  "_id": "ObjectId",
  "filename": "refund_policy.pdf",
  "original_name": "RefundPolicy.pdf",
  "uploaded_by": "ObjectId → users",
  "uploaded_at": "2026-07-01T09:00:00Z",
  "file_size_bytes": 204800,
  "chunk_count": 42,
  "is_indexed": true,
  "last_indexed_at": "2026-07-01T09:01:30Z"
}
```

---

## MongoDB Indexes — Full List

```javascript
// users
db.users.createIndex({ email: 1 }, { unique: true })
db.users.createIndex({ reset_token: 1 }, { sparse: true })

// sessions
db.sessions.createIndex({ session_id: 1 }, { unique: true })
db.sessions.createIndex({ user_id: 1 })
db.sessions.createIndex({ updated_at: -1 })

// conversations
db.conversations.createIndex({ session_id: 1 }, { unique: true })

// analytics
db.analytics.createIndex({ date: 1 })
db.analytics.createIndex({ user_id: 1 })
db.analytics.createIndex({ agents_used: 1 })

// tickets
db.tickets.createIndex({ ticket_id: 1 }, { unique: true })
db.tickets.createIndex({ status: 1 })
db.tickets.createIndex({ user_id: 1 })
```

---

## database/conversation.py — CRUD Operations

```python
from backend.database.mongo import db
from datetime import datetime


async def create_session(user_id: str, session_id: str, first_message: str):
    await db.sessions.insert_one({
        "session_id": session_id,
        "user_id": user_id,
        "title": first_message[:60],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_resolved": False,
        "ticket_id": None,
    })


async def append_turn(session_id: str, role: str, content: str,
                      agents_used=None, response_time_ms=None):
    turn = {
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if agents_used:
        turn["agents_used"] = agents_used
    if response_time_ms:
        turn["response_time_ms"] = response_time_ms

    await db.conversations.update_one(
        {"session_id": session_id},
        {"$push": {"turns": turn}},
        upsert=True,
    )
    await db.sessions.update_one(
        {"session_id": session_id},
        {"$set": {"updated_at": datetime.utcnow()}},
    )


async def get_history(session_id: str, last_n: int = 10):
    doc = await db.conversations.find_one({"session_id": session_id})
    if not doc:
        return []
    return doc["turns"][-last_n:]


async def get_user_sessions(user_id: str, limit: int = 20):
    cursor = db.sessions.find(
        {"user_id": user_id}
    ).sort("updated_at", -1).limit(limit)
    return await cursor.to_list(length=limit)
```
