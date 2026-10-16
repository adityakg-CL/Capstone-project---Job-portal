from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from middleware.dependencies import current_user, require_roles
from models.database import get_database
from models.schemas.domain import InterviewCreate, InterviewUpdate, FeedbackCreate
from utils.common import now_utc, serialize, audit, notify

router = APIRouter(prefix="/interviews", tags=["interviews"])

@router.post("", status_code=201)
def schedule(payload: InterviewCreate, user=Depends(require_roles("hiring_manager", "hr_admin"))):
    if not ObjectId.is_valid(payload.application_id): raise HTTPException(404, "Application not found")
    if payload.scheduled_at.tzinfo is None: raise HTTPException(422, "scheduled_at must include a timezone offset")
    db = get_database(); app = db.applications.find_one({"_id": ObjectId(payload.application_id)})
    if not app: raise HTTPException(404, "Application not found")
    job = db.jobs.find_one({"_id": ObjectId(app["job_id"])})
    if not job or (user["role"] != "hr_admin" and job["owner_id"] != user["id"]): raise HTTPException(403, "Forbidden")
    doc = {"application_id": payload.application_id, "job_id": app["job_id"], "employee_id": app["employee_id"],
           "owner_id": user["id"], "scheduled_at": payload.scheduled_at, "timezone": payload.timezone,
           "participants": payload.participants, "notes": payload.notes, "status": "scheduled",
           "feedback": [], "created_at": now_utc(), "updated_at": now_utc()}
    result = db.interviews.insert_one(doc)
    db.applications.update_one({"_id": app["_id"]}, {"$set": {"status": "interview", "updated_at": now_utc()}, "$push": {"status_history": {"status": "interview", "actor_id": user["id"], "at": now_utc()}}})
    audit(db, user["id"], "interview.schedule", "interview", result.inserted_id)
    notify(db, app["employee_id"], "interview_scheduled", "Interview scheduled", f"An interview was scheduled for {app['job_title']}.", "interview", result.inserted_id)
    return {"interview": serialize(db.interviews.find_one({"_id": result.inserted_id}))}

@router.get("")
def list_interviews(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), user=Depends(current_user)):
    db = get_database()
    if user["role"] == "employee": query = {"employee_id": user["id"]}
    elif user["role"] == "hiring_manager": query = {"owner_id": user["id"]}
    else: query = {}
    total = db.interviews.count_documents(query)
    return {"items": [serialize(d) for d in db.interviews.find(query).sort("scheduled_at", 1).skip((page-1)*page_size).limit(page_size)],
            "page": page, "page_size": page_size, "total": total}

@router.patch("/{interview_id}")
def update_interview(interview_id: str, payload: InterviewUpdate, user=Depends(require_roles("hiring_manager", "hr_admin"))):
    if not ObjectId.is_valid(interview_id): raise HTTPException(404, "Interview not found")
    db = get_database(); query = {"_id": ObjectId(interview_id)}
    if user["role"] != "hr_admin": query["owner_id"] = user["id"]
    interview = db.interviews.find_one(query)
    if not interview: raise HTTPException(404, "Interview not found")
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("scheduled_at") and changes["scheduled_at"].tzinfo is None: raise HTTPException(422, "scheduled_at must include a timezone offset")
    db.interviews.update_one(query, {"$set": {**changes, "updated_at": now_utc()}})
    if changes.get("status") == "cancelled":
        notify(db, interview["employee_id"], "interview_cancelled", "Interview cancelled", "Your interview was cancelled.", "interview", interview_id)
    audit(db, user["id"], "interview.update", "interview", interview_id, changes={k: True for k in changes})
    return {"interview": serialize(db.interviews.find_one(query))}

@router.post("/{interview_id}/feedback")
def feedback(interview_id: str, payload: FeedbackCreate, user=Depends(require_roles("hiring_manager", "hr_admin"))):
    if not ObjectId.is_valid(interview_id): raise HTTPException(404, "Interview not found")
    db = get_database(); query = {"_id": ObjectId(interview_id)}
    if user["role"] != "hr_admin": query["owner_id"] = user["id"]
    interview = db.interviews.find_one(query)
    if not interview: raise HTTPException(404, "Interview not found")
    entry = {**payload.model_dump(), "actor_id": user["id"], "created_at": now_utc()}
    db.interviews.update_one(query, {"$push": {"feedback": entry}, "$set": {"updated_at": now_utc()}})
    audit(db, user["id"], "interview.feedback", "interview", interview_id)
    return {"message": "Feedback recorded"}
