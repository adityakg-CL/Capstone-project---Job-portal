from pymongo import ASCENDING, DESCENDING
from models.database import get_database

def ensure_indexes() -> None:
    db = get_database()
    db.users.create_index([("email_normalized", ASCENDING)], unique=True, name="users_email_unique")
    db.jobs.create_index([("status", ASCENDING), ("created_at", DESCENDING)], name="jobs_status_created")
    db.jobs.create_index([("team", ASCENDING), ("location", ASCENDING)], name="jobs_team_location")
    # Manage Jobs filters by owner + status and sorts by creation date.
    db.jobs.create_index([("owner_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
                         name="jobs_owner_status_created")
    db.applications.create_index([("employee_id", ASCENDING), ("created_at", DESCENDING)], name="applications_employee")
    db.applications.create_index([("job_id", ASCENDING), ("status", ASCENDING)], name="applications_job_status")
    # Dashboard "recent applicants" and applicant counts query by job + recency.
    db.applications.create_index([("job_id", ASCENDING), ("created_at", DESCENDING)], name="applications_job_created")
    db.applications.create_index([("employee_id", ASCENDING), ("job_id", ASCENDING)], unique=True, name="applications_employee_job_unique")
    db.referrals.create_index([("referrer_id", ASCENDING), ("created_at", DESCENDING)], name="referrals_owner")
    db.referrals.create_index([("normalized_candidate_email", ASCENDING), ("job_id", ASCENDING)], name="referrals_candidate_job")
    # Referral queue and dashboard counts filter by job + status.
    db.referrals.create_index([("job_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
                              name="referrals_job_status_created")
    db.referral_bonuses.create_index([("referral_id", ASCENDING)], unique=True, name="bonus_referral_unique")
    db.referral_bonuses.create_index([("approval_status", ASCENDING), ("payment_status", ASCENDING)], name="bonus_status")
    db.interviews.create_index([("application_id", ASCENDING), ("scheduled_at", ASCENDING)], name="interviews_application_time")
    db.notifications.create_index([("recipient_id", ASCENDING), ("read_at", ASCENDING), ("created_at", DESCENDING)], name="notifications_recipient_read")
    db.audit_logs.create_index([("actor_id", ASCENDING), ("created_at", DESCENDING)], name="audit_actor_time")
    db.audit_logs.create_index([("entity_type", ASCENDING), ("entity_id", ASCENDING), ("created_at", DESCENDING)], name="audit_entity_time")
    db.business_rules.create_index([("key", ASCENDING)], unique=True, name="business_rules_key_unique")


def migrate_job_statuses(db) -> None:
    """Normalize legacy states without publishing jobs that were not active."""
    db.jobs.update_many(
        {"status": {"$in": ["active", "published"]}},
        {"$set": {"status": "open"}},
    )
    db.jobs.update_many(
        {"status": {"$nin": ["open", "closed"]}},
        {"$set": {"status": "closed"}},
    )
