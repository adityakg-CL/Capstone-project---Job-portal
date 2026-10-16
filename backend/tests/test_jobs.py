from copy import deepcopy
from types import SimpleNamespace

import pytest
from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient

from controllers import jobs as jobs_controller
from middleware.dependencies import current_user
from models.indexes import migrate_job_statuses


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, field, direction):
        self.documents.sort(key=lambda doc: doc.get(field), reverse=direction < 0)
        return self

    def skip(self, amount):
        self.documents = self.documents[amount:]
        return self

    def limit(self, amount):
        self.documents = self.documents[:amount]
        return self

    def __iter__(self):
        return iter(self.documents)


class FakeCollection:
    def __init__(self, documents=None):
        self.documents = documents or []

    @staticmethod
    def matches(document, query):
        for key, expected in query.items():
            if key == "$or":
                if not any(FakeCollection.matches(document, branch) for branch in expected):
                    return False
                continue
            actual = document.get(key)
            if isinstance(expected, dict):
                if "$in" in expected and actual not in expected["$in"]:
                    return False
                if "$nin" in expected and actual in expected["$nin"]:
                    return False
                if "$regex" in expected:
                    import re

                    flags = re.IGNORECASE if expected.get("$options") == "i" else 0
                    if not re.search(expected["$regex"], str(actual or ""), flags):
                        return False
            elif actual != expected:
                return False
        return True

    def find_one(self, query):
        return next((deepcopy(doc) for doc in self.documents if self.matches(doc, query)), None)

    def find(self, query=None, projection=None):
        documents = [deepcopy(doc) for doc in self.documents if self.matches(doc, query or {})]
        if projection:
            fields = {key for key, include in projection.items() if include}
            documents = [{key: value for key, value in doc.items() if key in fields or key == "_id"} for doc in documents]
        return FakeCursor(documents)

    def count_documents(self, query):
        return sum(1 for doc in self.documents if self.matches(doc, query))

    def insert_one(self, document):
        stored = deepcopy(document)
        stored.setdefault("_id", ObjectId())
        self.documents.append(stored)
        return SimpleNamespace(inserted_id=stored["_id"])

    def update_one(self, query, update):
        document = next((doc for doc in self.documents if self.matches(doc, query)), None)
        if document is None:
            return SimpleNamespace(modified_count=0)
        changed = any(document.get(key) != value for key, value in update["$set"].items())
        document.update(update["$set"])
        return SimpleNamespace(modified_count=int(changed))

    def update_many(self, query, update):
        modified = 0
        for document in self.documents:
            if self.matches(document, query):
                document.update(update["$set"])
                modified += 1
        return SimpleNamespace(modified_count=modified)

    def aggregate(self, pipeline):
        job_ids = pipeline[0]["$match"]["job_id"]["$in"]
        counts = {}
        for document in self.documents:
            if document.get("job_id") in job_ids:
                counts[document["job_id"]] = counts.get(document["job_id"], 0) + 1
        return [{"_id": job_id, "count": count} for job_id, count in counts.items()]


class FakeDatabase:
    def __init__(self, jobs=None):
        self.jobs = FakeCollection(jobs)
        self.applications = FakeCollection()
        self.referrals = FakeCollection()
        self.audit_logs = FakeCollection()
        self.notifications = FakeCollection()


@pytest.fixture
def manager_client(monkeypatch):
    user = {"id": str(ObjectId()), "role": "hiring_manager"}
    db = FakeDatabase()
    app = FastAPI()
    app.include_router(jobs_controller.router)
    app.dependency_overrides[current_user] = lambda: user
    monkeypatch.setattr(jobs_controller, "get_database", lambda: db)
    monkeypatch.setattr(jobs_controller, "audit", lambda *args, **kwargs: None)
    monkeypatch.setattr(jobs_controller, "notify", lambda *args, **kwargs: None)
    return TestClient(app), db, user, app


def test_create_list_close_and_reopen_job(manager_client):
    client, db, user, _ = manager_client
    response = client.post("/jobs", json={
        "title": "Senior Product Designer",
        "team": "Product",
        "location": "Remote",
        "description": "Build useful product experiences for our internal teams.",
        "skills": ["Design"],
    })
    assert response.status_code == 201
    job = response.json()["job"]
    assert job["status"] == "open"
    assert job["owner_id"] == user["id"]

    job_id = job["id"]
    db.applications.insert_one({"job_id": job_id, "employee_id": "employee-1"})
    db.referrals.insert_one({"job_id": job_id, "candidate_name": "Candidate"})

    assert client.get("/jobs/managed").json()["total"] == 1
    listed = client.get("/jobs/managed?status=open").json()
    assert listed["total"] == 1
    assert listed["items"][0]["status"] == "open"
    assert listed["items"][0]["applicant_count"] == 1

    closed = client.patch(f"/jobs/{job_id}/status", json={"status": "closed"})
    assert closed.status_code == 200
    assert closed.json()["job"]["status"] == "closed"
    assert client.get("/jobs/managed").json()["items"][0]["status"] == "closed"
    assert client.get("/jobs/managed?status=open").json()["total"] == 0
    assert client.get("/jobs/managed?status=closed").json()["items"][0]["status"] == "closed"

    reopened = client.patch(f"/jobs/{job_id}/status", json={"status": "open"})
    assert reopened.status_code == 200
    assert reopened.json()["job"]["status"] == "open"
    refreshed = client.get("/jobs/managed?status=open").json()
    assert refreshed["total"] == 1
    assert refreshed["items"][0]["status"] == "open"
    assert len(db.applications.documents) == 1
    assert len(db.referrals.documents) == 1


def test_job_status_api_rejects_unauthorized_and_legacy_values(manager_client):
    client, db, user, app = manager_client
    job_id = ObjectId()
    db.jobs.insert_one({"_id": job_id, "owner_id": user["id"], "title": "Role", "status": "open"})

    app.dependency_overrides[current_user] = lambda: {"id": str(ObjectId()), "role": "employee"}
    assert client.patch(f"/jobs/{job_id}/status", json={"status": "closed"}).status_code == 403

    app.dependency_overrides[current_user] = lambda: {"id": str(ObjectId()), "role": "hiring_manager"}
    assert client.patch(f"/jobs/{job_id}/status", json={"status": "closed"}).status_code == 404
    app.dependency_overrides[current_user] = lambda: user
    assert client.patch(f"/jobs/{job_id}/status", json={"status": "published"}).status_code == 422


def test_legacy_status_migration_preserves_jobs_and_relationship_data():
    statuses = ["active", "published", "approved", "pending_approval", "draft", "rejected", "archived", "closed"]
    jobs = [
        {"_id": ObjectId(), "status": status, "application_ids": ["application"], "referral_ids": ["referral"]}
        for status in statuses
    ]
    db = FakeDatabase(jobs)

    migrate_job_statuses(db)

    assert len(db.jobs.documents) == len(statuses)
    assert [job["status"] for job in db.jobs.documents] == ["open"] * 2 + ["closed"] * 6
    assert all(job["application_ids"] == ["application"] for job in db.jobs.documents)
    assert all(job["referral_ids"] == ["referral"] for job in db.jobs.documents)
