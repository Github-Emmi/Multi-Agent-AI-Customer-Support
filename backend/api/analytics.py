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
