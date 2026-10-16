from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from middleware.dependencies import current_user, require_roles
from models.database import get_database
from models.schemas.domain import ReferralCreate, ReferralStatusUpdate, BonusDecision, BonusPaymentUpdate
from utils.common import now_utc, serialize, audit, notify, user_directory

router = APIRouter(tags=["referrals"])

# Referral workflow statuses. "pending" is the only state that still needs a
# hiring manager's review; eligibility and bonus amounts are decided separately.
REFERRAL_STATUSES = ("pending", "eligible", "ineligible", "interview", "offered", "hired", "rejected")
# A manager may move a referral between these review states only.
MANAGER_REFERRAL_TRANSITIONS = {
    "pending": {"eligible", "ineligible"},
    "eligible": {"ineligible"},
    "ineligible": {"eligible"},
}


def _managed_job_ids(db, user: dict) -> list[str]:
    if user["role"] == "hr_admin":
        return []
    return [str(job["_id"]) for job in db.jobs.find({"owner_id": user["id"]}, {"_id": 1})]


def _referral_scope(db, user: dict) -> dict:
    """Referrals visible to the caller: HR sees all, managers only their own jobs."""
    if user["role"] == "hr_admin":
        return {}
    return {"job_id": {"$in": _managed_job_ids(db, user)}}


def _decorate(db, referrals: list[dict]) -> list[dict]:
    """Attach real referrer, job title and bonus status to each referral.

    All three joins use one query each for the whole page instead of per-row
    lookups, and missing related records render as null rather than crashing.
    """
    people = user_directory(db, [ref.get("referrer_id") for ref in referrals])
    job_ids = [ref.get("job_id") for ref in referrals]
    object_ids = []
    for value in job_ids:
        text = str(value) if value is not None else ""
        if text and ObjectId.is_valid(text):
            object_ids.append(ObjectId(text))
    titles = {}
    if object_ids:
        titles = {str(job["_id"]): job.get("title")
                  for job in db.jobs.find({"_id": {"$in": list(dict.fromkeys(object_ids))}}, {"title": 1})}
    bonuses = {}
    referral_ids = [str(ref["_id"]) for ref in referrals]
    if referral_ids:
        bonuses = {str(bonus["referral_id"]): {
            "id": str(bonus["_id"]),
            "approval_status": bonus.get("approval_status"),
            "payment_status": bonus.get("payment_status"),
            "amount": bonus.get("amount"),
            "currency": bonus.get("currency"),
        } for bonus in db.referral_bonuses.find({"referral_id": {"$in": referral_ids}})}

    decorated = []
    for ref in referrals:
        item = serialize(ref)
        referrer = people.get(str(ref.get("referrer_id")))
        item["referrer"] = {
            "id": referrer["id"] if referrer else ref.get("referrer_id"),
            "full_name": referrer["full_name"] if referrer else None,
            "email": referrer["email"] if referrer else None,
            "title": referrer["title"] if referrer else None,
            "team": referrer["team"] if referrer else None,
        }
        item["job_title"] = titles.get(str(ref.get("job_id"))) if ref.get("job_id") else None
        item["bonus"] = bonuses.get(str(ref["_id"]))
        decorated.append(item)
    return decorated


@router.post("/referrals", status_code=201)
def create_referral(payload: ReferralCreate, user=Depends(current_user)):
    if user["role"] != "employee": raise HTTPException(403, "Only employees can submit referrals")
    db = get_database(); email = str(payload.candidate_email).lower().strip()
    job_id = payload.job_id
    if job_id:
        if not ObjectId.is_valid(job_id): raise HTTPException(404, "Job not found")
        if not db.jobs.find_one({"_id": ObjectId(job_id), "status": "open"}): raise HTTPException(409, "Referral job must be open")
    dup = db.referrals.find_one({"normalized_candidate_email": email, "job_id": job_id})
    if dup: raise HTTPException(409, "A referral for this candidate and job already exists")
    doc = {"referrer_id": user["id"], "candidate_name": payload.candidate_name.strip(),
           "candidate_email": email, "normalized_candidate_email": email, "job_id": job_id,
           "status": "pending", "note": payload.note,
           "status_history": [{"status": "pending", "actor_id": user["id"], "at": now_utc()}],
           "created_at": now_utc(), "updated_at": now_utc()}
    result = db.referrals.insert_one(doc)
    audit(db, user["id"], "referral.create", "referral", result.inserted_id)
    return {"referral": serialize(db.referrals.find_one({"_id": result.inserted_id}))}

@router.get("/referrals/me")
def my_referrals(q: str | None = None, status: str | None = None,
                 page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), user=Depends(current_user)):
    db = get_database(); query = {"referrer_id": user["id"]}
    if status:
        if status not in REFERRAL_STATUSES:
            raise HTTPException(422, f"Unknown referral status: {status}")
        query["status"] = status
    if q:
        query["$or"] = [{"candidate_name": {"$regex": q, "$options": "i"}},
                        {"candidate_email": {"$regex": q, "$options": "i"}}]
    total = db.referrals.count_documents(query)
    documents = list(db.referrals.find(query).sort("created_at", -1).skip((page-1)*page_size).limit(page_size))
    return {"items": _decorate(db, documents), "page": page, "page_size": page_size,
            "total": total, "total_pages": max(1, -(-total // page_size))}

@router.get("/referrals/{referral_id}")
def referral_detail(referral_id: str, user=Depends(current_user)):
    if not ObjectId.is_valid(referral_id): raise HTTPException(404, "Referral not found")
    db = get_database(); referral = db.referrals.find_one({"_id": ObjectId(referral_id)})
    if not referral: raise HTTPException(404, "Referral not found")
    _assert_referral_visible(db, user, referral)
    return {"referral": _decorate(db, [referral])[0]}


def _assert_referral_visible(db, user: dict, referral: dict) -> None:
    """Employees see only their own referrals; managers only those on their jobs."""
    if user["role"] == "employee":
        if referral["referrer_id"] != user["id"]:
            raise HTTPException(403, "Forbidden")
        return
    if user["role"] == "hiring_manager":
        job_id = referral.get("job_id")
        job = db.jobs.find_one({"_id": ObjectId(job_id)}) if job_id and ObjectId.is_valid(job_id) else None
        if not job or job.get("owner_id") != user["id"]:
            raise HTTPException(403, "Forbidden")


@router.get("/admin/referrals")
def all_referrals(q: str | None = None, status: str | None = None,
                  page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                  user=Depends(require_roles("hr_admin", "hiring_manager"))):
    db = get_database(); query = _referral_scope(db, user)
    if status:
        if status not in REFERRAL_STATUSES:
            raise HTTPException(422, f"Unknown referral status: {status}")
        query["status"] = status
    if q:
        query["$or"] = [{"candidate_name": {"$regex": q, "$options": "i"}},
                        {"candidate_email": {"$regex": q, "$options": "i"}}]
    total = db.referrals.count_documents(query)
    documents = list(db.referrals.find(query).sort("created_at", -1).skip((page-1)*page_size).limit(page_size))
    return {"items": _decorate(db, documents), "page": page, "page_size": page_size,
            "total": total, "total_pages": max(1, -(-total // page_size))}

@router.patch("/admin/referrals/{referral_id}/status")
def update_referral_status(referral_id: str, payload: ReferralStatusUpdate,
                           user=Depends(require_roles("hiring_manager", "hr_admin"))):
    """Record a review decision on a referral.

    Only review transitions are allowed here. Eligibility never implies a bonus
    amount: the HR bonus-decision endpoint remains the only place an amount is set.
    """
    if not ObjectId.is_valid(referral_id): raise HTTPException(404, "Referral not found")
    db = get_database(); referral = db.referrals.find_one({"_id": ObjectId(referral_id)})
    if not referral: raise HTTPException(404, "Referral not found")
    _assert_referral_visible(db, user, referral)
    if user["role"] != "hr_admin":
        allowed = MANAGER_REFERRAL_TRANSITIONS.get(referral["status"], set())
        if payload.status not in allowed:
            raise HTTPException(409, f"Cannot move a {referral['status']} referral to {payload.status}")
    entry = {"status": payload.status, "actor_id": user["id"], "at": now_utc(), "reason": payload.reason}
    result = db.referrals.update_one(
        {"_id": referral["_id"], "status": referral["status"]},
        {"$set": {"status": payload.status, "eligibility_reason": payload.reason, "updated_at": now_utc()},
         "$push": {"status_history": entry}})
    if not result.modified_count:
        raise HTTPException(409, "Referral changed; refresh and retry")
    audit(db, user["id"], "referral.status.update", "referral", referral_id, changes={"status": payload.status})
    notify(db, referral["referrer_id"], "referral_status", "Referral status updated",
           f"Your referral is now marked {payload.status}.", "referral", referral_id)
    updated = db.referrals.find_one({"_id": referral["_id"]})
    return {"referral": _decorate(db, [updated])[0]}

@router.post("/admin/referrals/{referral_id}/eligibility")
def set_referral_eligibility(referral_id: str, eligible: bool, reason: str | None = None, user=Depends(require_roles("hr_admin"))):
    if not ObjectId.is_valid(referral_id): raise HTTPException(404, "Referral not found")
    db = get_database(); referral = db.referrals.find_one({"_id": ObjectId(referral_id)})
    if not referral: raise HTTPException(404, "Referral not found")
    status = "eligible" if eligible else "ineligible"
    entry = {"status": status, "actor_id": user["id"], "at": now_utc(), "reason": reason}
    db.referrals.update_one({"_id": referral["_id"]},
        {"$set": {"status": status, "eligibility_reason": reason, "updated_at": now_utc()},
         "$push": {"status_history": entry}})
    # No bonus amount or automatic eligibility rule is assumed. HR must explicitly
    # create/approve a bonus through the bonus-decision endpoint.
    audit(db, user["id"], "referral.eligibility", "referral", referral_id, changes={"status": status})
    notify(db, referral["referrer_id"], "referral_status", "Referral status updated", f"Your referral is now marked {status}.", "referral", referral_id)
    updated = db.referrals.find_one({"_id": referral["_id"]})
    return {"referral": _decorate(db, [updated])[0]}

@router.post("/admin/referrals/{referral_id}/bonus-decision")
def decide_bonus(referral_id: str, payload: BonusDecision, user=Depends(require_roles("hr_admin"))):
    if not ObjectId.is_valid(referral_id): raise HTTPException(404, "Referral not found")
    db = get_database(); referral = db.referrals.find_one({"_id": ObjectId(referral_id)})
    if not referral: raise HTTPException(404, "Referral not found")
    bonus = db.referral_bonuses.find_one({"referral_id": referral_id})
    if payload.decision == "approved" and payload.amount is None:
        raise HTTPException(422, "An explicit amount is required to approve a bonus; no default amount is configured")
    if bonus and bonus.get("approval_status") in ("approved", "paid"):
        raise HTTPException(409, "Bonus decision is already finalized")
    doc = {"referral_id": referral_id, "referrer_id": referral["referrer_id"],
           "approval_status": payload.decision, "payment_status": "not_started",
           "amount": payload.amount if payload.decision == "approved" else None,
           "currency": payload.currency.upper(), "reason": payload.reason,
           "approved_by": user["id"], "updated_at": now_utc()}
    if bonus:
        db.referral_bonuses.update_one({"_id": bonus["_id"]}, {"$set": doc})
        bonus_id = bonus["_id"]
    else:
        doc["created_at"] = now_utc()
        bonus_id = db.referral_bonuses.insert_one(doc).inserted_id
    audit(db, user["id"], "bonus.decision", "referral_bonus", bonus_id, changes={"decision": payload.decision, "amount": payload.amount})
    notify(db, referral["referrer_id"], "bonus_status", "Referral bonus decision", f"Your referral bonus was {payload.decision}.", "referral_bonus", bonus_id)
    return {"bonus": serialize(db.referral_bonuses.find_one({"_id": bonus_id}))}

@router.patch("/admin/bonuses/{bonus_id}/payment")
def update_bonus_payment(bonus_id: str, payload: BonusPaymentUpdate, user=Depends(require_roles("hr_admin"))):
    if not ObjectId.is_valid(bonus_id): raise HTTPException(404, "Bonus not found")
    db = get_database(); bonus = db.referral_bonuses.find_one({"_id": ObjectId(bonus_id)})
    if not bonus: raise HTTPException(404, "Bonus not found")
    if bonus.get("approval_status") != "approved": raise HTTPException(409, "Only approved bonuses can be processed")
    if payload.payment_status == "paid" and not payload.reference:
        raise HTTPException(422, "A payment reference is required to mark a bonus paid")
    db.referral_bonuses.update_one({"_id": bonus["_id"]}, {"$set": {"payment_status": payload.payment_status, "payment_reference": payload.reference, "updated_at": now_utc()}})
    audit(db, user["id"], "bonus.payment.update", "referral_bonus", bonus_id, changes={"payment_status": payload.payment_status})
    notify(db, bonus["referrer_id"], "bonus_payment", "Referral bonus payment updated", f"Payment tracking status: {payload.payment_status}.", "referral_bonus", bonus_id)
    return {"bonus": serialize(db.referral_bonuses.find_one({"_id": bonus["_id"]}))}

@router.get("/admin/referral-bonuses")
def list_bonuses(q: str | None = None, approval_status: str | None = None,
                 page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                 user=Depends(require_roles("hr_admin", "hiring_manager"))):
    """Bonus records with their referral and referrer context.

    A hiring manager sees bonuses for referrals on jobs they own; HR sees all.
    """
    db = get_database()
    query = {}
    if user["role"] != "hr_admin":
        managed = _managed_job_ids(db, user)
        query["referral_id"] = {"$in": [str(r["_id"]) for r in db.referrals.find(
            {"job_id": {"$in": managed}}, {"_id": 1})]}
    if approval_status:
        query["approval_status"] = approval_status
    if q:
        query["$or"] = [{"referrer_id": {"$regex": q, "$options": "i"}},
                        {"payment_reference": {"$regex": q, "$options": "i"}}]
    total = db.referral_bonuses.count_documents(query)
    documents = list(db.referral_bonuses.find(query).sort("created_at", -1)
                     .skip((page-1)*page_size).limit(page_size))
    referral_ids = [str(bonus["referral_id"]) for bonus in documents]
    referrals = {str(ref["_id"]): ref for ref in db.referrals.find(
        {"_id": {"$in": [ObjectId(i) for i in referral_ids if ObjectId.is_valid(i)]}})} if referral_ids else {}
    people = user_directory(db, [bonus.get("referrer_id") for bonus in documents])
    items = []
    for bonus in documents:
        item = serialize(bonus)
        referral = referrals.get(str(bonus["referral_id"]))
        referrer = people.get(str(bonus.get("referrer_id")))
        item["candidate_name"] = referral.get("candidate_name") if referral else None
        item["job_id"] = referral.get("job_id") if referral else None
        item["referral_status"] = referral.get("status") if referral else None
        item["referrer"] = {
            "id": referrer["id"] if referrer else bonus.get("referrer_id"),
            "full_name": referrer["full_name"] if referrer else None,
            "email": referrer["email"] if referrer else None,
        }
        items.append(item)
    return {"items": items, "page": page, "page_size": page_size, "total": total,
            "total_pages": max(1, -(-total // page_size))}


@router.get("/referral-bonuses/me")
def my_bonuses(user=Depends(current_user)):
    db = get_database()
    documents = list(db.referral_bonuses.find({"referrer_id": user["id"]}).sort("created_at", -1))
    referral_ids = [str(bonus["referral_id"]) for bonus in documents]
    referrals = {str(ref["_id"]): ref for ref in db.referrals.find(
        {"_id": {"$in": [ObjectId(i) for i in referral_ids if ObjectId.is_valid(i)]}})} if referral_ids else {}
    return {"items": [{
        **serialize(bonus),
        "candidate_name": (referrals.get(str(bonus["referral_id"])) or {}).get("candidate_name"),
        "job_id": (referrals.get(str(bonus["referral_id"])) or {}).get("job_id"),
        "referral_status": (referrals.get(str(bonus["referral_id"])) or {}).get("status"),
    } for bonus in documents]}
