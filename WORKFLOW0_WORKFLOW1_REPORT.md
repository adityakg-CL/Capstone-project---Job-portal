# Workflow 0 + Workflow 1 Report — Auth regression, job details, application submission

Date UTC: 2026-10-13
Git: NOT INITIALIZED, no Git status available. No unrelated work could be
reviewed through Git; only Phase 2 files were touched.

## Workflow 0 baseline and verification

Relevant files:

- `frontend/src/services/api.ts`
- `frontend/src/context/AuthContext.tsx`
- `frontend/src/App.tsx`
- `backend/controllers/auth.py`
- `backend/controllers/jobs.py`
- `backend/config/config.py`

Findings:

- `/api/v1` is applied exactly once.
  Backend mounts `api_router` at `settings.api_v1_prefix=/api/v1`;
  frontend `VITE_API_BASE_URL` already includes `/api/v1`.
- Previous auth/jobs claims were accurate except interactive browser testing.
- Isolated test database is now available:
  `cirruslabs_talenthub_test` on local MongoDB.
- No browser automation tool is connected in this environment.
  Composio search returned an unrelated ClickUp QA plan, not browser testing.

Actual Workflow 0 checks on isolated test DB port 8002:

- Health: PASS.
- Register employee: PASS, role `employee`.
- Login plus `/auth/me`: PASS.
- Published jobs list: PASS.
- Wrong password: PASS, HTTP 401.
- Invalid bearer: PASS, HTTP 401.
- Logout then reuse old token: PASS, `/auth/me` returns HTTP 401.
- Dev data untouched: PASS.
- Test cleanup removed only `w0.emp.*`: PASS.
- Existing backend tests: PASS, 4/4.
- Frontend build: PASS.
- Interactive browser login/refresh/logout: NOT TESTED, no browser tool connected.

## Workflow 1 implementation

Relevant existing APIs reused:

- `GET /api/v1/jobs/{job_id}`
- `POST /api/v1/jobs/{job_id}/applications`
- `GET /api/v1/applications/me`
- Existing `ApplicationCreate` schema with `cover_note <= 5000`.
- Existing duplicate protection via unique employee/job index.
- Existing unpublished-job protection requiring `status=published`.
- Existing employee-only application permission.

Intended changes made, smallest reasonable scope:

1. Added application types and API methods to `frontend/src/services/api.ts`.
2. Added separate `JobDetailApi` in `frontend/src/App.tsx`.
   Existing demo `JobDetail` was preserved for fallback.
3. Wired job-card selection through existing `selectedJobId`.
4. Added job loading, unavailable, apply success, and apply error states.
5. Added optional cover-note input with 5000-character client validation.
6. Preserved Figma layout and navigation.

Important changes:

- `frontend/src/services/api.ts`:
  added `ApiApplication`, `ApplicationsResponse`, `applyToJob`, `myApplications`.
- `frontend/src/App.tsx`:
  added `JobDetailApi`; route now uses it whenever a real job ID is selected.
  Demo content remains only when no ID exists.
- `frontend/dist/*`: regenerated build output.
- No backend changes.
- No resume-upload feature added; none exists in backend requirements.

Tests needed and executed against isolated test DB:

- Seed manager/admin/test job and publish it: PASS.
- Fresh employee sees one published job: PASS.
- Fetch job detail by ID: PASS.
- Valid application submission: PASS, status `submitted`.
- Employee history total: PASS, total 1.
- Duplicate apply: PASS, HTTP 409.
- Oversize cover note: PASS, HTTP 422.
- Invalid job ID apply: PASS, HTTP 404.
- Unauthenticated apply: PASS, HTTP 401.
- Manager apply: PASS, correctly rejected HTTP 403.
- Draft/closed job apply: PASS, HTTP 404.
- Database persistence verified: PASS, one test application persisted.
- Dev database untouched: PASS.
- Existing backend tests: PASS, 4/4.
- Frontend build: PASS.
- Page-refresh persistence through browser: NOT TESTED, no browser tool.
- Browser console/network inspection: NOT TESTED, no browser tool.

## Changed files

- `frontend/src/services/api.ts`
- `frontend/src/App.tsx`
- `frontend/dist/*`
- `WORKFLOW0_WORKFLOW1_REPORT.md`

## Commands executed

- `pytest -q` in `backend`
- `npm run build` in `frontend`
- Backend health checks on ports 8001/8002
- Register/login/me/jobs/job-detail/apply/history API checks
- Duplicate, invalid, unauthorized, unpublished-job negative API checks
- Direct MongoDB persistence and cleanup checks

## Known issues and next step

- No Git repository exists, so change preservation relies on filesystem scope.
- No browser automation is connected; browser journey remains unverified.
- Test DB now exists but has no automated fixtures/cleanup script yet.
- Next step: Workflow 2, employee applications and hiring-manager review.
  STOPPING HERE per instruction; awaiting direction before Workflow 2.
