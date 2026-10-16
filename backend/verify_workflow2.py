"""Workflow 2 end-to-end verification against an isolated test server.

Covers: resume upload/download/replace/delete, employee application history,
hiring-manager applicant review (list/detail/status), and authorization.

Usage (from backend/):
  $env:MONGODB_DATABASE='cirruslabs_talenthub_test'
  uvicorn main:app --port 8002   (separate shell)
  python verify_workflow2.py                 # run all checks (leaves data for restart test)
  python verify_workflow2.py --resume-only   # quick re-check after server restart
  python verify_workflow2.py --cleanup       # remove all w2-* test data
"""
import json
import os
import sys
import time

import httpx
from pymongo import MongoClient

BASE = os.environ.get("VERIFY_BASE", "http://127.0.0.1:8002/api/v1").rstrip("/")
DB_NAME = os.environ.get("MONGODB_DATABASE", "cirruslabs_talenthub_test")
MONGO_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage", "resumes")
STATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_workflow2.state.json")
PASSWORD = "Passw0rd!w2"
W2_EMAIL = {"$regex": r"^w2-.*@cirruslabs\.io$"}

results: list[tuple[str, bool]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, bool(cond)))
    line = f"{'PASS' if cond else 'FAIL'}  {name}"
    if detail and not cond:
        line += f"  -> {detail}"
    print(line, flush=True)


def pdf_bytes(marker: str) -> bytes:
    body = f"%PDF-1.4\n%workflow2-{marker}\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
    return body.encode()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def register(client: httpx.Client, label: str) -> tuple[str, str]:
    email = f"w2-{label}-{RUN}@cirruslabs.io"
    r = client.post("/auth/register", json={"full_name": f"W2 {label}", "email": email, "password": PASSWORD})
    r.raise_for_status()
    r = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    r.raise_for_status()
    return email, r.json()["access_token"]


def promote(db, email: str, role: str) -> None:
    db.users.update_one({"email_normalized": email}, {"$set": {"role": role}})


def cleanup(db) -> None:
    users = list(db.users.find({"email_normalized": W2_EMAIL}, {"_id": 1, "resume.storage_name": 1}))
    ids = [u["_id"] for u in users]
    job_ids = [j["_id"] for j in db.jobs.find({"title": {"$regex": "^W2 "}}, {"_id": 1})]
    for u in users:
        name = (u.get("resume") or {}).get("storage_name")
        if name and "/" not in name and "\\" not in name:
            try:
                os.unlink(os.path.join(STORAGE, name))
            except OSError:
                pass
    db.applications.delete_many({"job_id": {"$in": [str(j) for j in job_ids]}})
    db.applications.delete_many({"employee_id": {"$in": [str(i) for i in ids]}})
    db.jobs.delete_many({"title": {"$regex": "^W2 "}})
    db.notifications.delete_many({"user_id": {"$in": [str(i) for i in ids]}})
    db.audit_logs.delete_many({"actor_id": {"$in": [str(i) for i in ids]}})
    db.audit_logs.delete_many({"entity_id": {"$in": [str(j) for j in job_ids]}})
    db.users.delete_many({"email_normalized": W2_EMAIL})
    print(f"cleanup: removed users={len(users)} jobs={len(job_ids)} from {DB_NAME}")


RUN = str(int(time.time()))


def main() -> int:
    mongo = MongoClient(MONGO_URI)
    db = mongo[DB_NAME]
    if "--cleanup" in sys.argv:
        cleanup(db)
        return 0

    client = httpx.Client(base_url=BASE, timeout=30.0)

    if "--resume-only" in sys.argv:
        with open(STATE, encoding="utf-8") as fh:
            emp_email = json.load(fh)["emp_email"]
        r = client.post("/auth/login", json={"email": emp_email, "password": PASSWORD})
        r.raise_for_status()
        emp_tok = r.json()["access_token"]
        r = client.get("/users/me/resume", headers=auth_headers(emp_tok))
        check("resume-only: metadata present after restart", r.status_code == 200, r.text[:200])
        r = client.get("/users/me/resume/download", headers=auth_headers(emp_tok))
        check("resume-only: download after restart", r.status_code == 200 and r.content.startswith(b"%PDF-"), r.text[:200])
        return finish()

    emp_email, emp_tok = register(client, "emp")
    mgr_email, mgr_tok = register(client, "mgr1")
    mgr2_email, mgr2_tok = register(client, "mgr2")
    hr_email, hr_tok = register(client, "hr")
    promote(db, mgr_email, "hiring_manager")
    promote(db, mgr2_email, "hiring_manager")
    promote(db, hr_email, "hr_admin")
    with open(STATE, "w", encoding="utf-8") as fh:
        json.dump({"emp_email": emp_email}, fh)
    emp_id = client.get("/users/me", headers=auth_headers(emp_tok)).json()["user"]["id"]

    r = client.post("/jobs", headers=auth_headers(mgr_tok), json={
        "title": f"W2 Workflow Role {RUN}", "team": "Product & Design", "location": "Bengaluru",
        "description": "Workflow 2 verification role used by the automated checks.",
        "skills": ["Figma", "Research"],
    })
    r.raise_for_status()
    job_id = r.json()["job"]["id"]
    check("new job starts open", r.json()["job"]["status"] == "open", str(r.json()["job"].get("status")))
    r = client.get("/jobs/managed?status=open", headers=auth_headers(mgr_tok))
    check("manager lists open job", r.status_code == 200 and any(job["id"] == job_id for job in r.json()["items"]), r.text[:200])
    r = client.patch(f"/jobs/{job_id}/status", headers=auth_headers(mgr_tok), json={"status": "closed"})
    check("manager closes job", r.status_code == 200 and r.json()["job"]["status"] == "closed", r.text[:200])
    r = client.patch(f"/jobs/{job_id}/status", headers=auth_headers(mgr_tok), json={"status": "open"})
    check("manager reopens job", r.status_code == 200 and r.json()["job"]["status"] == "open", r.text[:200])
    print(f"seeded: job={job_id} db={DB_NAME}")

    r = client.get("/users/me/resume", headers=auth_headers(emp_tok))
    check("metadata before upload -> 404", r.status_code == 404, str(r.status_code))
    r = client.get("/users/me/resume/download", headers=auth_headers(emp_tok))
    check("download before upload -> 404", r.status_code == 404, str(r.status_code))
    r = client.post("/users/me/resume", headers=auth_headers(emp_tok), files={"file": ("resume.txt", b"plain", "text/plain")})
    check("non-.pdf filename -> 422", r.status_code == 422, str(r.status_code))
    r = client.post("/users/me/resume", headers=auth_headers(emp_tok), files={"file": ("resume.pdf", b"not a pdf at all", "application/pdf")})
    check("fake pdf content -> 422", r.status_code == 422, str(r.status_code))
    r = client.post("/users/me/resume", headers=auth_headers(emp_tok), files={"file": ("resume.pdf", b"", "application/pdf")})
    check("empty file -> 422", r.status_code == 422, str(r.status_code))
    r = client.post("/users/me/resume", headers=auth_headers(emp_tok), files={"file": ("big.pdf", b"%PDF-1.4\n" + b"0" * (5 * 1024 * 1024 + 1) + b"\n%%EOF", "application/pdf")})
    check("oversize >5MB -> 413", r.status_code == 413, str(r.status_code))

    pdf1 = pdf_bytes("one")
    r = client.post("/users/me/resume", headers=auth_headers(emp_tok), files={"file": ("avery-resume.pdf", pdf1, "application/pdf")})
    ok = r.status_code == 200
    meta1 = r.json().get("user", {}).get("resume") if ok else None
    check("upload valid pdf -> 200", ok, r.text[:300])
    check("upload returns metadata only (no storage_name)",
          ok and set(meta1 or {}) == {"filename", "content_type", "size_bytes", "uploaded_at"}, str(meta1))
    check("metadata filename preserved", ok and meta1 and meta1["filename"] == "avery-resume.pdf", str(meta1))
    r = client.get("/users/me", headers=auth_headers(emp_tok))
    check("GET /users/me includes resume", r.status_code == 200 and r.json()["user"].get("resume") is not None, r.text[:200])
    r = client.get("/users/me/resume/download", headers=auth_headers(emp_tok))
    check("download own resume -> 200 pdf bytes", r.status_code == 200 and r.content == pdf1, f"{r.status_code} len={len(r.content)}")
    check("download content-type application/pdf", "application/pdf" in r.headers.get("content-type", ""), r.headers.get("content-type", ""))
    check("download content-disposition filename", "avery-resume.pdf" in r.headers.get("content-disposition", ""), r.headers.get("content-disposition", ""))
    disk = os.listdir(STORAGE) if os.path.isdir(STORAGE) else []
    check("pdf persisted to resume storage", len(disk) >= 1, str(disk))

    pdf2 = pdf_bytes("two-longer-content")
    r = client.post("/users/me/resume", headers=auth_headers(emp_tok), files={"file": ("avery-v2.pdf", pdf2, "application/pdf")})
    meta2 = r.json().get("user", {}).get("resume") if r.status_code == 200 else None
    check("replace upload -> 200", r.status_code == 200, r.text[:300])
    check("replace updates size metadata", meta2 and meta2["size_bytes"] == len(pdf2), str(meta2))
    check("old storage file unlinked after replace", len(os.listdir(STORAGE)) == 1, str(os.listdir(STORAGE)))
    r = client.get("/users/me/resume/download", headers=auth_headers(emp_tok))
    check("download after replace returns new bytes", r.content == pdf2, f"len={len(r.content)}")

    r = client.delete("/users/me/resume", headers=auth_headers(emp_tok))
    check("delete -> 200", r.status_code == 200, str(r.status_code))
    r = client.get("/users/me/resume", headers=auth_headers(emp_tok))
    check("metadata after delete -> 404", r.status_code == 404, str(r.status_code))
    r = client.get("/users/me/resume/download", headers=auth_headers(emp_tok))
    check("download after delete -> 404", r.status_code == 404, str(r.status_code))
    r = client.delete("/users/me/resume", headers=auth_headers(emp_tok))
    check("delete again -> 404", r.status_code == 404, str(r.status_code))
    disk_after = os.listdir(STORAGE) if os.path.isdir(STORAGE) else []
    check("file unlinked from storage on delete", disk_after == [], str(disk_after))
    emp_doc = db.users.find_one({"email_normalized": {"$regex": f"^w2-emp-{RUN}@"}}, {"resume": 1})
    check("user doc has no resume field after delete", emp_doc.get("resume") is None, str(emp_doc.get("resume")))

    r = client.post("/users/me/resume", headers=auth_headers(emp_tok), files={"file": ("avery-resume.pdf", pdf1, "application/pdf")})
    check("re-upload for review tests", r.status_code == 200, r.text[:200])
    # ---- Application history + manager review ----
    r = client.post(f"/jobs/{job_id}/applications", headers=auth_headers(emp_tok), json={"cover_note": "Workflow 2 test application"})
    check("employee applies -> 201", r.status_code == 201, r.text[:200])
    app_id = r.json()["application"]["id"]

    r = client.get("/applications/me", headers=auth_headers(emp_tok))
    body = r.json() if r.status_code == 200 else {}
    mine = [a for a in body.get("items", []) if a["id"] == app_id]
    check("history lists application", r.status_code == 200 and mine, r.text[:200])
    check("history item has status_history", bool(mine) and mine[0].get("status_history"), str(mine and mine[0]))

    r = client.get(f"/applications/{app_id}", headers=auth_headers(emp_tok))
    check("employee detail of own application -> 200", r.status_code == 200, str(r.status_code))

    r = client.get(f"/jobs/{job_id}/applications", headers=auth_headers(mgr_tok))
    items = r.json().get("items", []) if r.status_code == 200 else []
    check("manager lists job applications -> 200", r.status_code == 200 and any(a["id"] == app_id for a in items), r.text[:200])
    r = client.get(f"/jobs/{job_id}/applications", headers=auth_headers(mgr2_tok))
    check("other manager list -> 403", r.status_code == 403, str(r.status_code))
    r = client.get(f"/jobs/{job_id}/applications", headers=auth_headers(emp_tok))
    check("employee list of applicants -> 403", r.status_code == 403, str(r.status_code))

    r = client.get(f"/applications/{app_id}", headers=auth_headers(mgr_tok))
    check("manager detail includes status_history", r.status_code == 200 and len(r.json()["application"].get("status_history", [])) >= 1, r.text[:200])
    r = client.get(f"/applications/{app_id}", headers=auth_headers(mgr2_tok))
    check("other manager detail -> 403", r.status_code == 403, str(r.status_code))

    r = client.get(f"/users/{emp_id}/resume/download", headers=auth_headers(mgr_tok))
    check("manager downloads applicant resume -> 200 pdf", r.status_code == 200 and r.content == pdf1, f"{r.status_code} len={len(r.content)}")
    check("applicant resume content-type", "application/pdf" in r.headers.get("content-type", ""), r.headers.get("content-type", ""))
    r = client.get(f"/users/{emp_id}/resume/download", headers=auth_headers(mgr2_tok))
    check("cross-manager resume download -> 403", r.status_code == 403, str(r.status_code))
    r = client.get(f"/users/{emp_id}/resume/download", headers=auth_headers(emp_tok))
    check("non-manager resume download -> 403", r.status_code == 403, str(r.status_code))

    r = client.patch(f"/applications/{app_id}/status", headers=auth_headers(mgr_tok), json={"status": "under_review"})
    check("submitted -> under_review -> 200", r.status_code == 200, r.text[:200])
    r = client.patch(f"/applications/{app_id}/status", headers=auth_headers(mgr_tok), json={"status": "shortlisted"})
    check("under_review -> shortlisted -> 200", r.status_code == 200, r.text[:200])
    r = client.patch(f"/applications/{app_id}/status", headers=auth_headers(mgr_tok), json={"status": "under_review"})
    check("invalid shortlisted -> under_review -> 409", r.status_code == 409, str(r.status_code))
    r = client.patch(f"/applications/{app_id}/status", headers=auth_headers(mgr2_tok), json={"status": "rejected"})
    check("other manager status update -> 403", r.status_code == 403, str(r.status_code))
    r = client.get(f"/applications/{app_id}", headers=auth_headers(emp_tok))
    hist = r.json()["application"].get("status_history", [])
    check("status_history records 3 transitions", len(hist) == 3, str([h["status"] for h in hist]))

    r = client.post(f"/applications/{app_id}/withdraw", headers=auth_headers(emp_tok))
    check("employee withdraws shortlisted application -> 200", r.status_code == 200, r.text[:200])
    r = client.get("/applications/me", headers=auth_headers(emp_tok))
    mine = [a for a in r.json().get("items", []) if a["id"] == app_id]
    check("withdrawn visible in history", mine and mine[0]["status"] == "withdrawn", str(mine))
    return finish()


def finish() -> int:
    passed = sum(1 for _, ok in results if ok)
    failed = [(n, ) for n, ok in results if not ok]
    print(f"\n{passed}/{len(results)} checks passed")
    if failed:
        print("failed:", failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

