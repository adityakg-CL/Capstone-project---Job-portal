from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from middleware.dependencies import current_user
from models.database import get_database
from utils.common import now_utc, serialize

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("")
def list_notifications(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), unread_only: bool = False, user=Depends(current_user)):
    db = get_database(); query = {"recipient_id": user["id"]}
    if unread_only: query["read_at"] = None
    total = db.notifications.count_documents(query)
    unread = db.notifications.count_documents({"recipient_id": user["id"], "read_at": None})
    return {"items": [serialize(d) for d in db.notifications.find(query).sort("created_at", -1).skip((page-1)*page_size).limit(page_size)],
            "page": page, "page_size": page_size, "total": total, "unread_count": unread}

@router.patch("/{notification_id}/read")
def mark_read(notification_id: str, user=Depends(current_user)):
    if not ObjectId.is_valid(notification_id): raise HTTPException(404, "Notification not found")
    result = get_database().notifications.update_one({"_id": ObjectId(notification_id), "recipient_id": user["id"]}, {"$set": {"read_at": now_utc()}})
    if not result.matched_count: raise HTTPException(404, "Notification not found")
    return {"message": "Notification marked read"}

@router.post("/read-all")
def read_all(user=Depends(current_user)):
    result = get_database().notifications.update_many({"recipient_id": user["id"], "read_at": None}, {"$set": {"read_at": now_utc()}})
    return {"message": "Notifications marked read", "updated": result.modified_count}
