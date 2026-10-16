from fastapi import APIRouter, Depends, Query
from middleware.dependencies import current_user, require_roles
from models.database import get_database
from utils.common import serialize

router = APIRouter(prefix="/admin", tags=["HR/Admin"])

@router.get("/dashboard", dependencies=[Depends(require_roles("hr_admin"))])
def dashboard(user=Depends(current_user)):
    db = get_database()
    return {"users": db.users.count_documents({"is_active": True}),
            "open_jobs": db.jobs.count_documents({"status": "open"}),
            "applications": db.applications.count_documents({}),
            "pending_bonuses": db.referral_bonuses.count_documents({"approval_status": "approved", "payment_status": {"$in": ["not_started", "processing", "on_hold"]}})}

@router.get("/audit-logs", dependencies=[Depends(require_roles("hr_admin"))])
def audit_logs(page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100),
               actor_id: str | None = None, entity_type: str | None = None, action: str | None = None, user=Depends(current_user)):
    db = get_database(); query = {}
    if actor_id: query["actor_id"] = actor_id
    if entity_type: query["entity_type"] = entity_type
    if action: query["action"] = {"$regex": action, "$options": "i"}
    total = db.audit_logs.count_documents(query)
    return {"items": [serialize(d) for d in db.audit_logs.find(query).sort("created_at", -1).skip((page-1)*page_size).limit(page_size)],
            "page": page, "page_size": page_size, "total": total}
