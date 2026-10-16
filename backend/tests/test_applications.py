from copy import deepcopy
from types import SimpleNamespace

import pytest
from bson import ObjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError, PyMongoError

from controllers import applications as applications_controller
from controllers import jobs as jobs_controller
from middleware.dependencies import current_user


class Cursor:
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


class Collection:
    def __init__(self, documents=None):
        self.documents = documents or []
        self.insert_error = None

    @staticmethod
    def matches(document, query):
        return all(document.get(key) == value for key, value in query.items())

    def find_one(self, query):
        document = next((doc for doc in self.documents if self.matches(doc, query)), None)
        return deepcopy(document) if document else None

    def find(self, query=None, projection=None):
        documents = [deepcopy(doc) for doc in self.documents if self.matches(doc, query or {})]
        if projection:
            fields = {key for key, include in projection.items() if include}
            documents = [{key: value for key, value in doc.items() if key in fields or key == "_id"} for doc in documents]
        return Cursor(documents)

    def count_documents(self, query):
        return sum(self.matches(doc, query) for doc in self.documents)

    def insert_one(self, document):
        if self.insert_error:
            raise self.insert_error
        stored = deepcopy(document)
        if any(
            existing.get("employee_id") == stored.get("employee_id")
            and existing.get("job_id") == stored.get("job_id")
            for existing in self.documents
        ):
            raise DuplicateKeyError("duplicate employee/job application")
        stored["_id"] = ObjectId()
        self.documents.append(stored)
        return SimpleNamespace(inserted_id=stored["_id"])

    def aggregate(self, pipeline):
        job_ids = pipeline[0]["$match"]["job_id"]["$in"]
        counts = {}
        for document in self.documents:
            if document.get("job_id") in job_ids:
                counts[document["job_id"]] = counts.get(document["job_id"], 0) + 1
        return [{"_id": job_id, "count": count} for job_id, count in counts.items()]


class Database:
    def __init__(self, job):
        self.jobs = Collection([job])
        self.applications = Collection()
        self.users = Collection()
        self.audit_logs = Collection()
        self.notifications = Collection()


@pytest.fixture
def application_client(monkeypatch):
    employee = {"id": str(ObjectId()), "role": "employee"}
    manager = {"id": str(ObjectId()), "role": "hiring_manager"}
    job = {
        "_id": ObjectId(),
        "title": "Product Designer",
        "status": "open",
        "owner_id": manager["id"],
        "created_at": 1,
    }
    db = Database(job)
    user_state = {"current": employee}
    app = FastAPI()
    app.include_router(jobs_controller.router)
    app.include_router(applications_controller.router)
    app.dependency_overrides[current_user] = lambda: user_state["current"]
    monkeypatch.setattr(jobs_controller, "get_database", lambda: db)
    monkeypatch.setattr(applications_controller, "get_database", lambda: db)
    monkeypatch.setattr(applications_controller, "audit", lambda *args, **kwargs: None)
    monkeypatch.setattr(applications_controller, "notify", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        applications_controller,
        "user_directory",
        lambda _db, _ids: {
            employee["id"]: {
                "id": employee["id"],
                "full_name": "Test Employee",
                "email": "employee@cirruslabs.io",
                "title": "Designer",
                "team": "Product",
            }
        },
    )
    return TestClient(app), db, employee, manager, job, user_state, app


def test_employee_application_is_visible_in_both_workspaces(application_client):
    client, db, employee, manager, job, user_state, _ = application_client
    response = client.post(
        f"/jobs/{job['_id']}/applications",
        json={"cover_note": "I am interested in this role."},
    )

    assert response.status_code == 201
    application = response.json()["application"]
    assert application["job_id"] == str(job["_id"])
    assert application["employee_id"] == employee["id"]
    assert application["job_title"] == job["title"]
    assert application["status"] == "submitted"
    assert application["created_at"]
    assert application["status_history"][0]["status"] == "submitted"

    my_applications = client.get(f"/applications/me?job_id={job['_id']}")
    assert my_applications.status_code == 200
    assert my_applications.json()["total"] == 1
    assert my_applications.json()["items"][0]["id"] == application["id"]

    user_state["current"] = manager
    applicants = client.get(f"/jobs/{job['_id']}/applications")
    assert applicants.status_code == 200
    assert applicants.json()["total"] == 1
    assert applicants.json()["items"][0]["applicant"]["id"] == employee["id"]

    managed_jobs = client.get("/jobs/managed")
    assert managed_jobs.status_code == 200
    assert managed_jobs.json()["items"][0]["applicant_count"] == 1
    assert len(db.applications.documents) == 1


def test_duplicate_closed_and_invalid_job_applications_are_rejected(application_client):
    client, db, _employee, _manager, job, _user_state, _app = application_client
    path = f"/jobs/{job['_id']}/applications"
    assert client.post(path, json={}).status_code == 201
    duplicate = client.post(path, json={})
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "You have already applied to this job"

    job["status"] = "closed"
    assert client.post(f"/jobs/{job['_id']}/applications", json={}).status_code == 404
    assert client.post("/jobs/not-an-object-id/applications", json={}).status_code == 404
    assert client.post(f"/jobs/{ObjectId()}/applications", json={}).status_code == 404
    assert len(db.applications.documents) == 1


def test_unauthenticated_application_is_rejected(application_client):
    client, _db, _employee, _manager, job, _user_state, app = application_client
    app.dependency_overrides.clear()

    response = client.post(f"/jobs/{job['_id']}/applications", json={})

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_non_employee_cannot_apply_and_duplicate_index_race_returns_conflict(application_client, monkeypatch):
    client, db, employee, manager, job, user_state, _app = application_client
    path = f"/jobs/{job['_id']}/applications"

    user_state["current"] = manager
    assert client.post(path, json={}).status_code == 403

    user_state["current"] = employee
    db.applications.documents.append({
        "_id": ObjectId(),
        "job_id": str(job["_id"]),
        "employee_id": employee["id"],
    })
    monkeypatch.setattr(db.applications, "find_one", lambda _query: None)

    duplicate = client.post(path, json={})

    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "You have already applied to this job"
    assert len(db.applications.documents) == 1


def test_audit_database_failure_does_not_report_a_saved_application_as_failed(application_client, monkeypatch, caplog):
    client, db, _employee, _manager, job, _user_state, _app = application_client

    def fail_audit(*_args, **_kwargs):
        raise PyMongoError("audit storage unavailable")

    monkeypatch.setattr(applications_controller, "audit", fail_audit)

    response = client.post(f"/jobs/{job['_id']}/applications", json={})

    assert response.status_code == 201
    assert len(db.applications.documents) == 1
    assert "Could not record audit event" in caplog.text


def test_application_database_failures_are_logged_and_return_service_error(application_client, monkeypatch, caplog):
    client, db, _employee, _manager, job, _user_state, _app = application_client
    db.applications.insert_error = PyMongoError("private database detail")

    response = client.post(f"/jobs/{job['_id']}/applications", json={})

    assert response.status_code == 503
    assert "private database detail" not in response.text
    assert "Could not create application for job" in caplog.text
    assert len(db.applications.documents) == 0

    db.applications.insert_error = None
    monkeypatch.setattr(
        applications_controller,
        "get_database",
        lambda: (_ for _ in ()).throw(RuntimeError("database unavailable")),
    )
    unavailable = client.post(f"/jobs/{job['_id']}/applications", json={})
    assert unavailable.status_code == 503
    assert "database unavailable" not in unavailable.text
