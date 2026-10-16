from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from middleware.dependencies import current_user, require_roles
from models.database import get_database
from models.schemas.domain import JobCreate, JobUpdate, JobStatusUpdate
from utils.common import now_utc, serialize, audit, notify

router = APIRouter(tags=["jobs"])
JOB_STATES = {"open", "closed"}
OPEN_JOB_STATUSES = ("open",)


def _owner_query(user: dict) -> dict:
    """Ownership filter: HR admins act on any requisition, managers only their own."""
    return {} if user["role"] == "hr_admin" else {"owner_id": user["id"]}


def _applicant_counts(db, job_ids) -> dict:
    """job_id -> application count in a single grouped query (no N+1 lookups)."""
    if not job_ids:
        return {}
    pipeline = [
        {"$match": {"job_id": {"$in": job_ids}}},
        {"$group": {"_id": "$job_id", "count": {"$sum": 1}}},
    ]
    return {str(row["_id"]): row["count"] for row in db.applications.aggregate(pipeline)}


def _load_owned_job(db, user: dict, job_id: str) -> dict:
    if not ObjectId.is_valid(job_id):
        raise HTTPException(404, "Job not found")
    job = db.jobs.find_one({"_id": ObjectId(job_id), **_owner_query(user)})
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/jobs")
def browse_jobs(q: str | None = None, team: str | None = None, location: str | None = None,
                page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                sort: str = "newest", user=Depends(current_user)):
    db = get_database()
    query = {"status": {"$in": list(OPEN_JOB_STATUSES)}}
    if team: query["team"] = {"$regex": team, "$options": "i"}
    if location: query["location"] = {"$regex": location, "$options": "i"}
    if q: query["$or"] = [{"title": {"$regex": q, "$options": "i"}}, {"description": {"$regex": q, "$options": "i"}}, {"skills": {"$elemMatch": {"$regex": q, "$options": "i"}}}]
    order = [("created_at", 1)] if sort == "oldest" else [("title", 1)] if sort == "title" else [("created_at", -1)]
    total = db.jobs.count_documents(query)
    items = [serialize(d) for d in db.jobs.find(query).sort(order).skip((page-1)*page_size).limit(page_size)]
    return {"items": items, "page": page, "page_size": page_size, "total": total}

@router.get("/jobs/managed")
def managed_jobs(q: str | None = None, status: str | None = None,
                 page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                 user=Depends(require_roles("hiring_manager", "hr_admin"))):
    """Requisitions the caller owns, with real applicant counts and pagination.

    The `total` reflects the filtered database result, so pagination always
    matches what is actually stored.
    """
    db = get_database()
    query = _owner_query(user)
    if status:
        if status not in JOB_STATES:
            raise HTTPException(422, f"Unknown job status: {status}")
        query["status"] = status
    if q:
        query["$or"] = [{"title": {"$regex": q, "$options": "i"}},
                        {"team": {"$regex": q, "$options": "i"}},
                        {"location": {"$regex": q, "$options": "i"}}]
    total = db.jobs.count_documents(query)
    documents = list(db.jobs.find(query).sort("created_at", -1).skip((page-1)*page_size).limit(page_size))
    counts = _applicant_counts(db, [str(doc["_id"]) for doc in documents])
    items = []
    for doc in documents:
        item = serialize(doc)
        item["applicant_count"] = counts.get(str(doc["_id"]), 0)
        items.append(item)
    pages = max(1, -(-total // page_size))
    return {"items": items, "page": page, "page_size": page_size, "total": total, "total_pages": pages}


@router.get("/jobs/{job_id}")
def job_detail(job_id: str, user=Depends(current_user)):
    if not ObjectId.is_valid(job_id): raise HTTPException(404, "Job not found")
    db = get_database()
    job = db.jobs.find_one({"_id": ObjectId(job_id)})
    if not job: raise HTTPException(404, "Job not found")
    is_manager = user["role"] in ("hr_admin", "hiring_manager")
    if job["status"] != "open" and not is_manager: raise HTTPException(404, "Job not found")
    item = serialize(job)
    item["applicant_count"] = _applicant_counts(db, [job_id]).get(job_id, 0)
    return {"job": item}


@router.post("/jobs", status_code=201)
def create_job(payload: JobCreate, user=Depends(require_roles("hiring_manager", "hr_admin"))):
    db = get_database()
    doc = payload.model_dump()
    # owner_id is always the authenticated caller: a client-supplied owner is
    # never accepted, so nobody can file a requisition under another manager.
    doc.update({"owner_id": user["id"], "status": "open", "created_at": now_utc(), "updated_at": now_utc()})
    result = db.jobs.insert_one(doc)
    audit(db, user["id"], "job.create", "job", result.inserted_id)
    created = db.jobs.find_one({"_id": result.inserted_id})
    return {"job": {**serialize(created), "applicant_count": 0}}

@router.patch("/jobs/{job_id}")
def update_job(job_id: str, payload: JobUpdate, user=Depends(require_roles("hiring_manager", "hr_admin"))):
    db = get_database()
    job = _load_owned_job(db, user, job_id)
    if job["status"] == "closed":
        raise HTTPException(409, "This job cannot be edited in its current state")
    changes = payload.model_dump(exclude_unset=True)
    if "skills" in changes:
        changes["skills"] = [s.strip() for s in (changes["skills"] or []) if str(s).strip()]
    if changes:
        db.jobs.update_one({"_id": job["_id"]}, {"$set": {**changes, "updated_at": now_utc()}})
        audit(db, user["id"], "job.update", "job", job_id, changes={k: True for k in changes})
    updated = db.jobs.find_one({"_id": job["_id"]})
    count = _applicant_counts(db, [job_id]).get(job_id, 0)
    return {"job": {**serialize(updated), "applicant_count": count}}

@router.patch("/jobs/{job_id}/status")
def update_job_status(job_id: str, payload: JobStatusUpdate, user=Depends(require_roles("hiring_manager", "hr_admin"))):
    """Open or close a job owned by the authenticated manager."""
    db = get_database()
    job = _load_owned_job(db, user, job_id)
    if payload.status != job["status"]:
        result = db.jobs.update_one(
            {"_id": job["_id"], "status": job["status"], **_owner_query(user)},
            {"$set": {"status": payload.status, "updated_at": now_utc()}},
        )
        if not result.modified_count:
            raise HTTPException(409, "Job changed; refresh and retry")
    else:
        result = None
    if result:
        audit(db, user["id"], "job.status.change", "job", job_id, changes={"status": payload.status})
    if payload.status == "closed" and job["status"] != "closed":
        notify(db, job["owner_id"], "job_closed", "Requisition closed", f"{job['title']} was closed.", "job", job_id)
    updated = db.jobs.find_one({"_id": job["_id"]})
    count = _applicant_counts(db, [job_id]).get(job_id, 0)
    return {"job": {**serialize(updated), "applicant_count": count}}

@router.delete("/jobs/{job_id}")
def delete_job(job_id: str, user=Depends(require_roles("hiring_manager", "hr_admin"))):
    """Remove a requisition that has no applications or referrals.

    A job that already attracted applications or referrals is closed instead of
    deleted, so historical records are never orphaned or silently destroyed.
    """
    db = get_database()
    job = _load_owned_job(db, user, job_id)
    linked_applications = db.applications.count_documents({"job_id": job_id})
    linked_referrals = db.referrals.count_documents({"job_id": job_id})
    if linked_applications or linked_referrals:
        raise HTTPException(409, "This job has applications or referrals; close it instead of deleting")
    db.jobs.delete_one({"_id": job["_id"]})
    audit(db, user["id"], "job.delete", "job", job_id)
    return {"message": "Job deleted"}

