from fastapi import APIRouter, Depends
from bson import ObjectId
from middleware.dependencies import current_user, require_roles
from models.database import get_database
from config.config import get_settings
from utils.common import serialize, user_directory

router = APIRouter(prefix="/dashboard", tags=["dashboards"])

# Metric definitions (documented so the numbers are reproducible):
#   open_jobs           -> jobs.status == "open".
#   applications_total  -> one count_documents() over the applications the
#                          caller manages. Applications are counted directly,
#                          never by joining applicants, so no record is double
#                          counted and no applicant is inflated.
#   referrals_to_review -> referrals still in status "pending" on jobs the
#                          caller manages, i.e. genuinely awaiting review.
#   bonuses_to_approve  -> referral_bonuses with no HR decision yet, plus
#                          eligible referrals that have no bonus record. Paid,
#                          approved and rejected bonuses are excluded.
ACTIVE_APPLICATION_STATUSES = ("submitted", "under_review", "shortlisted", "interview", "offered")
PENDING_BONUS_APPROVALS = ("pending", "pending_approval", "awaiting_approval", "not_decided")


def _managed_job_scope(user: dict) -> dict:
    """Job ownership filter: HR admins see every requisition, managers only theirs."""
    return {} if user["role"] == "hr_admin" else {"owner_id": user["id"]}


def _owned_job_ids(db, user: dict) -> list[str]:
    return [str(job["_id"]) for job in db.jobs.find(_managed_job_scope(user), {"_id": 1})]


def _application_scope(db, user: dict):
    """Returns (query, owned_job_ids, sees_everything)."""
    if user["role"] == "hr_admin":
        return {}, [], True
    job_ids = _owned_job_ids(db, user)
    # An empty list must match nothing, never everything.
    return {"job_id": {"$in": job_ids}}, job_ids, False


def _referral_scope(db, user: dict):
    if user["role"] == "hr_admin":
        return {}, [], True
    job_ids = _owned_job_ids(db, user)
    return {"job_id": {"$in": job_ids}}, job_ids, False


def _job_titles(db, job_ids) -> dict:
    """job_id -> title in a single query, tolerant of missing/legacy ids."""
    object_ids = []
    for value in job_ids or []:
        text = str(value) if value is not None else ""
        if text and ObjectId.is_valid(text):
            object_ids.append(ObjectId(text))
    if not object_ids:
        return {}
    titles = db.jobs.find({"_id": {"$in": list(dict.fromkeys(object_ids))}}, {"title": 1})
    return {str(job["_id"]): job.get("title") for job in titles}


def _bonus_map(db, referral_ids: list[str]) -> dict:
    """referral_id -> bonus summary, one query for the whole list."""
    if not referral_ids:
        return {}
    bonuses = db.referral_bonuses.find({"referral_id": {"$in": referral_ids}})
    return {
        str(bonus["referral_id"]): {
            "id": str(bonus["_id"]),
            "approval_status": bonus.get("approval_status"),
            "payment_status": bonus.get("payment_status"),
            "amount": bonus.get("amount"),
            "currency": bonus.get("currency"),
        }
        for bonus in bonuses
    }


def _pending_bonus_count(db, referrals_query: dict) -> int:
    """Bonuses genuinely awaiting a decision.

    Counts referral_bonuses that have never been decided, plus eligible
    referrals that still have no bonus record. A referral is never assumed to
    carry a bonus amount merely because it exists.
    """
    undecided = db.referral_bonuses.count_documents(
        {"approval_status": {"$in": list(PENDING_BONUS_APPROVALS)}})
    eligible = [str(ref["_id"]) for ref in db.referrals.find(
        {**referrals_query, "status": "eligible"}, {"_id": 1})]
    if not eligible:
        return undecided
    decided = {str(bonus["referral_id"]) for bonus in db.referral_bonuses.find(
        {"referral_id": {"$in": eligible}}, {"referral_id": 1})}
    return undecided + sum(1 for referral_id in eligible if referral_id not in decided)


@router.get("/employee")
def employee_dashboard(user=Depends(require_roles("employee"))):
    db = get_database()
    limit = get_settings().dashboard_recent_size
    own_applications = {"employee_id": user["id"]}
    own_referrals = {"referrer_id": user["id"]}
    recent_applications = list(db.applications.find(own_applications).sort("created_at", -1).limit(limit))
    recent_referrals = list(db.referrals.find(own_referrals).sort("created_at", -1).limit(limit))
    job_titles = _job_titles(db, [app.get("job_id") for app in recent_applications]
                             + [ref.get("job_id") for ref in recent_referrals])
    bonus_map = _bonus_map(db, [str(ref["_id"]) for ref in recent_referrals])
    return {
        "applications_total": db.applications.count_documents(own_applications),
        "applications_active": db.applications.count_documents(
            {**own_applications, "status": {"$in": list(ACTIVE_APPLICATION_STATUSES)}}),
        "referrals_total": db.referrals.count_documents(own_referrals),
        "referrals_pending": db.referrals.count_documents({**own_referrals, "status": "pending"}),
        "open_jobs": db.jobs.count_documents({"status": "open"}),
        "unread_notifications": db.notifications.count_documents({"recipient_id": user["id"], "read_at": None}),
        "recent_applications": [{
            "id": str(app["_id"]),
            "job_id": app.get("job_id"),
            "job_title": app.get("job_title") or job_titles.get(str(app.get("job_id"))) or "Internal role",
            "status": app.get("status"),
            "created_at": app.get("created_at"),
        } for app in recent_applications],
        "recent_referrals": [{
            "id": str(ref["_id"]),
            "candidate_name": ref.get("candidate_name"),
            "job_id": ref.get("job_id"),
            "job_title": job_titles.get(str(ref.get("job_id"))) if ref.get("job_id") else None,
            "status": ref.get("status"),
            "bonus": bonus_map.get(str(ref["_id"])),
            "created_at": ref.get("created_at"),
        } for ref in recent_referrals],
    }

@router.get("/hiring-manager")
def hiring_manager_dashboard(user=Depends(require_roles("hiring_manager", "hr_admin"))):
    db = get_database()
    limit = get_settings().dashboard_recent_size
    job_query = _managed_job_scope(user)
    applications_query, job_ids, sees_all = _application_scope(db, user)
    referrals_query, referral_job_ids, referrals_all = _referral_scope(db, user)

    can_query_applications = sees_all or bool(job_ids)
    can_query_referrals = referrals_all or bool(referral_job_ids)
    recent_applications = list(
        db.applications.find(applications_query).sort("created_at", -1).limit(limit)) if can_query_applications else []
    recent_referrals = list(
        db.referrals.find(referrals_query).sort("created_at", -1).limit(limit)) if can_query_referrals else []

    directory = user_directory(db, [app.get("employee_id") for app in recent_applications]
                               + [ref.get("referrer_id") for ref in recent_referrals])
    job_titles = _job_titles(db, [app.get("job_id") for app in recent_applications]
                             + [ref.get("job_id") for ref in recent_referrals])
    bonus_map = _bonus_map(db, [str(ref["_id"]) for ref in recent_referrals])

    def person(account_id):
        """Resolve a real person, or an explicit unknown marker for legacy ids."""
        entry = directory.get(str(account_id)) if account_id else None
        if entry:
            return {"id": entry["id"], "full_name": entry["full_name"], "email": entry["email"],
                    "title": entry["title"], "team": entry["team"]}
        return {"id": str(account_id) if account_id else None, "full_name": None,
                "email": None, "title": None, "team": None}

    return {
        "jobs_total": db.jobs.count_documents(job_query),
        "jobs_open": db.jobs.count_documents({**job_query, "status": "open"}),
        "applications_total": db.applications.count_documents(applications_query) if can_query_applications else 0,
        "applications_to_review": db.applications.count_documents(
            {**applications_query, "status": {"$in": ["submitted", "under_review"]}}) if can_query_applications else 0,
        "referrals_to_review": db.referrals.count_documents(
            {**referrals_query, "status": "pending"}) if can_query_referrals else 0,
        "bonuses_to_approve": _pending_bonus_count(db, referrals_query) if can_query_referrals else 0,
        "recent_applicants": [{
            "id": str(app["_id"]),
            "job_id": app.get("job_id"),
            "job_title": app.get("job_title") or job_titles.get(str(app.get("job_id"))) or "Internal role",
            "employee_id": app.get("employee_id"),
            "applicant": person(app.get("employee_id")),
            "status": app.get("status"),
            "created_at": app.get("created_at"),
        } for app in recent_applications],
        "referral_queue": [{
            "id": str(ref["_id"]),
            "candidate_name": ref.get("candidate_name"),
            "job_id": ref.get("job_id"),
            "job_title": job_titles.get(str(ref.get("job_id"))) if ref.get("job_id") else None,
            "referrer_id": ref.get("referrer_id"),
            "referrer": person(ref.get("referrer_id")),
            "status": ref.get("status"),
            "bonus": bonus_map.get(str(ref["_id"])),
            "created_at": ref.get("created_at"),
        } for ref in recent_referrals],
    }
