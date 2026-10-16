# Phase 2 — Workflow 2 Report

**Scope:** Employee application history, hiring-manager applicant review (list / detail / status), and secure resume upload / download / replace / delete on the existing FastAPI + PyMongo + React/Vite/TS stack.

**Date:** 2026-10-14 · **No Git repo** (filesystem diff only) · **Browser automation unavailable** (UI verified via compile + API-level testing only).

---

## 1. What shipped

### Backend

Resume helpers were added to `backend/utils/common.py` and config (`backend/config/config.py`): `resume_storage_dir` (`storage/resumes`, resolved against the backend root, outside `frontend/public`), `resume_max_size_bytes` (5 MB), plus `public_resume_metadata`, `safe_resume_filename`, `new_resume_storage_name`, `resolve_resume_storage`, `is_pdf_bytes`. `backend/.env.example` documents the two new settings.

`backend/controllers/users.py` gained the resume endpoints (routes were already registered via `routes/router.py`; no router changes needed):

| Endpoint | Behavior |
|---|---|
| `POST /users/me/resume` | Employee-only. Requires `.pdf` extension, non-empty body (422), ≤ 5 MB (413), PDF magic bytes `%PDF-` + `%%EOF` (422). Writes to a `.tmp` file then atomic `replace()`; UUID storage name; `$set`s metadata (`filename`, `content_type`, `size_bytes`, `uploaded_at` — **never** `storage_name`); unlinks the old file after replace; audit log entry. |
| `GET /users/me/resume` | Metadata only; 404 when none. |
| `GET /users/me/resume/download` | `FileResponse`, `application/pdf`, original sanitized filename via `Content-Disposition`. 404 when missing. |
| `DELETE /users/me/resume` | Optimistic concurrency: filter includes `resume.storage_name`, so a concurrent replace yields 409. `$unset`s metadata, unlinks file, audits. |
| `GET /users/{user_id}/resume/download` | Manager/HR only. `hr_admin` unrestricted; `hiring_manager` must own a job the employee actually applied to (`_can_manager_access_resume`) — otherwise 403. Path-traversal-safe resolution (`relative_to` check). |
| `GET /users/me` | Now also returns the resume metadata block. |

Application history / review endpoints (`backend/controllers/applications.py`) **already existed** and were verified rather than changed: `GET /applications/me`, `GET /applications/{id}` (employee-owner or owning-manager only), `POST /applications/{id}/withdraw`, `GET /jobs/{id}/applications` (owner-manager or hr_admin), `PATCH /applications/{id}/status` (state-machine transitions, 409 on invalid transition, optimistic `status` match, notification + audit).

### Frontend

- `frontend/src/services/api.ts`: added `ApiResume`, `ApiProfile`, `JobsResponse` (pre-existing missing type), `requestMultipart` and `downloadBlob` helpers, and the Workflow 2 methods: `getApplication`, `withdrawApplication`, `jobApplications`, `updateApplicationStatus`, `managedJobs`, `getProfile`, `uploadResume`, `resumeMetadata`, `downloadOwnResume`, `deleteResume`, `downloadApplicantResume`.
- `frontend/src/App.tsx` (Figma layout preserved; existing components untouched):
  - **`ApplicationsPanel`** (employee “My applications”): live `GET /applications/me` table with job, applied date, status pill, view-job action, and withdraw (enabled for `submitted` / `under_review` / `shortlisted`).
  - **`ApplicantsPanel`** (manager review): job selector from `GET /jobs/managed`, applicants table from `GET /jobs/{id}/applications`, applicant resume download (`GET /users/{id}/resume/download` via blob), and status updates via `PATCH /applications/{id}/status` with a select populated from the same transition map the backend enforces.
  - **`ResumeCard`** (employee profile): metadata display, PDF-only file input with client hint (server enforces 5 MB cap), download, replace, delete.
  - `DataPage` delegates to the new panels for `applications` / `applicants` screens; `Shell` passes the selected `jobId` and clears stale ids when opening Applicants from the sidebar.
- `backend/.gitignore`: added `storage/resumes/`, verify-script state/logs.

### Verification harness

`backend/verify_workflow2.py` — standalone end-to-end script (httpx + pymongo) with `--resume-only` (persistence re-check) and `--cleanup` modes. It registers/promotes its own users (role promotion via direct pymongo, per project rules), seeds a published job through the admin flow, and runs every check below.

---

## 2. Commands and results

Isolation: port **8002**, `$env:MONGODB_DATABASE='cirruslabs_talenthub_test'`. (A stale uvicorn from a previous session was found holding port 8002 and was killed before starting the fresh test server.)

```
python verify_workflow2.py            → 45/45 checks passed
```

Highlights (all PASS):

- **Resume validation:** metadata/download before upload → 404; non-`.pdf` name → 422; fake-PDF content → 422; empty file → 422; >5 MB → 413.
- **Upload:** valid PDF → 200; response carries only `filename/content_type/size_bytes/uploaded_at` (no `storage_name`); file persisted under UUID name in `backend/storage/resumes`.
- **Download:** exact byte round-trip; `Content-Type: application/pdf`; `Content-Disposition` carries the sanitized filename.
- **Replace:** 200; size metadata updated; **old file unlinked** (storage dir holds exactly one file); download returns the new bytes.
- **Delete:** 200; metadata → 404; download → 404; repeat delete → 404; file unlinked; user doc has no `resume` field.
- **History:** employee applies → 201; `GET /applications/me` lists it with `status_history`; own detail → 200.
- **Manager review:** owning manager lists job applications (200) and reads detail with `status_history`; status flow `submitted → under_review → shortlisted` → 200; invalid `shortlisted → under_review` → 409; `status_history` records exactly 3 transitions; employee withdraws a shortlisted application → 200 and it shows `withdrawn` in history.
- **Authorization:** other-manager list/detail/status → 403; employee list of applicants → 403; cross-manager resume download → 403; non-manager resume download → 403.
- **Persistence across restart:** server stopped and restarted → resume metadata + download still served (2/2 checks).

```
python -m pytest -q                   → 4 passed in 1.55s
npx tsc --noEmit                      → 0 errors
npm run build                         → ✓ built (vite 8.0.5)
```

**Isolation confirmed.** Dev DB `cirruslabs_talenthub` before and after: `users 6, jobs 1, applications 0, notifications 1, audit_logs 17, referrals 0, bonuses 0` — unchanged. Test DB has zero `w2-*` residue after `--cleanup`; `backend/storage/resumes` empty; server stopped (0 listeners on 8002); temp logs/state removed.

---

## 3. Untested / limitations

- **Browser interaction** (file-picker UX, blob download triggering, drawer navigation) — no browser automation available; UI verified by type-check, build, and the API contract the client calls. All API calls the components make were exercised directly by the verification script.
- Applicant rows show a truncated employee id (`Employee …XXXXXX`) because the backend exposes no applicant-name lookup for managers — adding one (e.g. `GET /admin/applicants/{id}`) is a reasonable Workflow 3 item.
- `PATCH /users/me` (profile fields) is out of Workflow 2 scope and still only updates the fields it always did.
- No rate limiting / antivirus scanning on uploads (PDF magic-byte validation only).

