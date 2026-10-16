import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, PyMongoError
from middleware.dependencies import current_user, require_roles
from models.database import get_database
from models.schemas.domain import ApplicationCreate, ApplicationStatusUpdate
from utils.common import now_utc, serialize, audit, notify, user_directory

router = APIRouter(tags=["applications"])
logger = logging.getLogger(__name__)
ALLOWED_TRANSITIONS = {
    "submitted": {"under_review", "shortlisted", "rejected"},
    "under_review": {"shortlisted", "interview", "offered", "rejected"},
    "shortlisted": {"interview", "offered", "rejected"},
    "interview": {"offered", "hired", "rejected"},
    "offered": {"hired", "rejected"},
}

@router.post("/jobs/{job_id}/applications", status_code=201)
def apply(job_id: str, payload: ApplicationCreate, user=Depends(current_user)):
    if user["role"] != "employee": raise HTTPException(403, "Only employees can apply to internal jobs")
    if not ObjectId.is_valid(job_id): raise HTTPException(404, "Job not found")
    try:
        db = get_database()
        job = db.jobs.find_one({"_id": ObjectId(job_id), "status": "open"})
        if not job:
            raise HTTPException(404, "Job not found or is not open for applications")
        existing = db.applications.find_one({"job_id": job_id, "employee_id": user["id"]})
        if existing:
            raise HTTPException(409, "You have already applied to this job")
        created_at = now_utc()
        doc = {
            "job_id": job_id,
            "job_title": job["title"],
            "employee_id": user["id"],
            "status": "submitted",
            "cover_note": payload.cover_note,
            "status_history": [{"status": "submitted", "actor_id": user["id"], "at": created_at}],
            "created_at": created_at,
            "updated_at": created_at,
        }
        result = db.applications.insert_one(doc)
    except HTTPException:
        raise
    except DuplicateKeyError:
        raise HTTPException(409, "You have already applied to this job")
    except (PyMongoError, RuntimeError) as exc:
        logger.exception("Could not create application for job %s", job_id)
        raise HTTPException(503, "Applications are temporarily unavailable. Please try again.") from exc
    try:
        audit(db, user["id"], "application.submit", "application", result.inserted_id)
    except PyMongoError:
        logger.exception("Could not record audit event for application %s", result.inserted_id)
    try:
        notify(db, job["owner_id"], "application_submitted", "New job application", f"An employee applied for {job['title']}.", "application", result.inserted_id)
    except PyMongoError:
        logger.exception("Could not notify the job owner about application %s", result.inserted_id)
    return {"application": serialize({"_id": result.inserted_id, **doc})}

@router.get("/applications/me")
def my_applications(job_id: str | None = None, page: int = Query(1, ge=1),
                    page_size: int = Query(20, ge=1, le=100), user=Depends(current_user)):
    if job_id is not None and not ObjectId.is_valid(job_id):
        raise HTTPException(404, "Job not found")
    db = get_database()
    query = {"employee_id": user["id"]}
    if job_id:
        query["job_id"] = job_id
    total = db.applications.count_documents(query)
    return {"items": [serialize(d) for d in db.applications.find(query).sort("created_at", -1).skip((page-1)*page_size).limit(page_size)],
            "page": page, "page_size": page_size, "total": total}

@router.get("/applications/{application_id}")
def application_detail(application_id: str, user=Depends(current_user)):
    if not ObjectId.is_valid(application_id): raise HTTPException(404, "Application not found")
    db = get_database(); app = db.applications.find_one({"_id": ObjectId(application_id)})
    if not app: raise HTTPException(404, "Application not found")
    if user["role"] == "employee" and app["employee_id"] != user["id"]: raise HTTPException(403, "Forbidden")
    if user["role"] == "hiring_manager":
        job = db.jobs.find_one({"_id": ObjectId(app["job_id"])})
        if not job or job.get("owner_id") != user["id"]: raise HTTPException(403, "Forbidden")
    return {"application": serialize(app)}

@router.post("/applications/{application_id}/withdraw")
def withdraw(application_id: str, user=Depends(current_user)):
    if user["role"] != "employee": raise HTTPException(403, "Only employees can withdraw applications")
    if not ObjectId.is_valid(application_id): raise HTTPException(404, "Application not found")
    db = get_database(); query = {"_id": ObjectId(application_id), "employee_id": user["id"], "status": {"$in": ["submitted", "under_review", "shortlisted"]}}
    doc = db.applications.find_one(query)
    if not doc: raise HTTPException(409, "Application cannot be withdrawn")
    result = db.applications.update_one(query, {"$set": {"status": "withdrawn", "updated_at": now_utc()}, "$push": {"status_history": {"status": "withdrawn", "actor_id": user["id"], "at": now_utc()}}})
    if not result.modified_count: raise HTTPException(409, "Application changed; refresh and retry")
    audit(db, user["id"], "application.withdraw", "application", application_id)
    return {"message": "Application withdrawn"}

@router.get("/jobs/{job_id}/applications")
def job_applications(job_id: str, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), user=Depends(require_roles("hiring_manager", "hr_admin"))):
    if not ObjectId.is_valid(job_id): raise HTTPException(404, "Job not found")
    db = get_database(); job = db.jobs.find_one({"_id": ObjectId(job_id)})
    if not job: raise HTTPException(404, "Job not found")
    if user["role"] != "hr_admin" and job["owner_id"] != user["id"]: raise HTTPException(403, "Forbidden")
    query = {"job_id": job_id}; total = db.applications.count_documents(query)
    documents = list(db.applications.find(query).sort("created_at", -1).skip((page-1)*page_size).limit(page_size))
    return {"items": _decorate(db, documents), "page": page, "page_size": page_size,
            "total": total, "total_pages": max(1, -(-total // page_size))}


def _decorate(db, documents: list[dict]) -> list[dict]:
    """Attach the real applicant identity to each application.

    Managers previously had to display a truncated employee id because no
    identity lookup existed; this resolves names in one query for the page.
    """
    directory = user_directory(db, [doc.get("employee_id") for doc in documents])
    items = []
    for doc in documents:
        item = serialize(doc)
        person = directory.get(str(doc.get("employee_id")))
        item["applicant"] = {
            "id": person["id"] if person else doc.get("employee_id"),
            "full_name": person["full_name"] if person else None,
            "email": person["email"] if person else None,
            "title": person["title"] if person else None,
            "team": person["team"] if person else None,
        }
        items.append(item)
    return items

@router.patch("/applications/{application_id}/status")
def update_status(application_id: str, payload: ApplicationStatusUpdate, user=Depends(require_roles("hiring_manager", "hr_admin"))):
    if not ObjectId.is_valid(application_id): raise HTTPException(404, "Application not found")
    db = get_database(); app = db.applications.find_one({"_id": ObjectId(application_id)})
    if not app: raise HTTPException(404, "Application not found")
    job = db.jobs.find_one({"_id": ObjectId(app["job_id"])})
    if not job or (user["role"] != "hr_admin" and job["owner_id"] != user["id"]): raise HTTPException(403, "Forbidden")
    if payload.status not in ALLOWED_TRANSITIONS.get(app["status"], set()): raise HTTPException(409, f"Invalid transition from {app['status']} to {payload.status}")
    entry = {"status": payload.status, "actor_id": user["id"], "at": now_utc(), "reason": payload.reason}
    result = db.applications.update_one({"_id": app["_id"], "status": app["status"]}, {"$set": {"status": payload.status, "updated_at": now_utc()}, "$push": {"status_history": entry}})
    if not result.modified_count: raise HTTPException(409, "Application changed; refresh and retry")
    audit(db, user["id"], "application.status.update", "application", application_id, changes={"status": payload.status})
    notify(db, app["employee_id"], "application_status", "Application updated", f"Your application for {app['job_title']} is now {payload.status}.", "application", application_id)
    return {"message": "Application status updated"}
