"""
Analytics API — /analytics/*
Aggregated metrics for the dashboard + satisfaction feedback.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends

from backend.api.auth import get_current_user
from backend.database.mongo import get_db
from backend.models.schemas import FeedbackRequest

router = APIRouter()


@router.get("/summary")
async def get_summary(user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = str(user["_id"])

    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": None,
                "total_conversations": {"$sum": 1},
                "avg_response_time": {"$avg": {"$avg": "$response_times"}},
                "avg_satisfaction": {"$avg": "$satisfaction_rating"},
            }
        },
    ]
    results = await db.analytics.aggregate(pipeline).to_list(1)
    if not results:
        return {
            "total_conversations": 0,
            "avg_response_time_ms": 0.0,
            "satisfaction_score": 0.0,
        }

    r = results[0]
    return {
        "total_conversations": r.get("total_conversations", 0),
        "avg_response_time_ms": round(r.get("avg_response_time") or 0, 1),
        "satisfaction_score": round(r.get("avg_satisfaction") or 0, 2),
    }


@router.get("/agent-usage")
async def get_agent_usage(user: dict = Depends(get_current_user)):
    db = get_db()
    user_id = str(user["_id"])

    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$unwind": "$agents_used_history"},
        {
            "$group": {
                "_id": "$agents_used_history",
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
    ]
    results = await db.analytics.aggregate(pipeline).to_list(10)
    return [{"agent": r["_id"], "count": r["count"]} for r in results]


@router.get("/daily")
async def get_daily_conversations(
    days: int = 7,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    user_id = str(user["_id"])
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    pipeline = [
        {"$match": {"user_id": user_id, "date": {"$gte": cutoff}}},
        {"$group": {"_id": "$date", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    results = await db.analytics.aggregate(pipeline).to_list(30)
    return [{"date": r["_id"], "count": r["count"]} for r in results]


@router.post("/feedback")
async def submit_feedback(
    body: FeedbackRequest,
    user: dict = Depends(get_current_user),
):
    db = get_db()
    await db.analytics.update_one(
        {"session_id": body.session_id},
        {
            "$set": {
                "satisfaction_rating": body.rating,
                "satisfaction_comment": body.comment,
            }
        },
    )
    return {"message": "Feedback recorded. Thank you!"}


# ── EN-09: Satisfaction Analytics ────────────────────────────────────────────

@router.get("/satisfaction")
async def get_satisfaction_distribution(user: dict = Depends(get_current_user)):
    """Return satisfaction rating distribution (count per 1-5 star rating)."""
    db = get_db()
    user_id = str(user["_id"])
    pipeline = [
        {"$match": {"user_id": user_id, "satisfaction_rating": {"$exists": True}}},
        {"$group": {"_id": "$satisfaction_rating", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    results = await db.analytics.aggregate(pipeline).to_list(5)
    dist = {str(i): 0 for i in range(1, 6)}
    for r in results:
        dist[str(r["_id"])] = r["count"]
    return {"distribution": dist}


@router.get("/tickets")
async def get_ticket_analytics(user: dict = Depends(get_current_user)):
    """Return ticket volume by status and resolution time stats."""
    db = get_db()
    user_id = str(user["_id"])
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    results = await db.tickets.aggregate(pipeline).to_list(10)
    by_status = {r["_id"]: r["count"] for r in results}
    total = sum(by_status.values())
    return {"total": total, "by_status": by_status}


@router.get("/sentiment")
async def get_sentiment_trends(user: dict = Depends(get_current_user)):
    """Return average sentiment score over the last 7 days."""
    db = get_db()
    user_id = str(user["_id"])
    cutoff = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    pipeline = [
        {"$match": {"user_id": user_id, "date": {"$gte": cutoff},
                    "sentiment_score": {"$exists": True}}},
        {"$group": {"_id": "$date", "avg_sentiment": {"$avg": "$sentiment_score"},
                    "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    results = await db.analytics.aggregate(pipeline).to_list(7)
    return [{"date": r["_id"], "avg_sentiment": round(r["avg_sentiment"], 2),
             "count": r["count"]} for r in results]
