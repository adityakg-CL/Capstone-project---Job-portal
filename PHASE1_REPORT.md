# Phase 1 Stabilization Report — CirrusLabs Internal Hiring Portal

Date (UTC): 2026-10-13
Scope: stabilize existing frontend + backend + MongoDB without rewriting working code.

## 1. Actual repository structure

- Root: README.md, placeholder package.json, stale pnpm-lock.yaml.
- `backend/main.py`: FastAPI ASGI app `main:app`.
- `backend/server.py`: dev launcher to port 8000.
- `backend/config/config.py`: pydantic-settings from `backend/.env`.
- `backend/models/database.py`: PyMongo connect/ping/close.
- `backend/models/indexes.py`: ensure_indexes on startup.
- `backend/models/schemas/`: auth + domain validation.
- `backend/controllers/`: auth, users, jobs, applications, referrals,
  interviews, notifications, admin, dashboard.
- `backend/routes/router.py`: api_router mounted at `/api/v1`.
- `backend/middleware/`: JWT + Bearer/cookie current_user + require_roles.
- `backend/tests/`: test_security.py, test_transitions.py.
- `backend/requirements.txt`, `pytest.ini`, `.env.example`.
- `backend/.env`: local-only, gitignored, generated JWT secret.
- `backend/.venv/`: Python 3.12.10, not committed.

Auth preserved: email/password + JWT bearer + HTTP-only cookie, roles
`employee | hiring_manager | hr_admin`. No OIDC/SSO in code; none added.
Referral, application, and bonus workflows preserved unchanged.

## 2. Startup commands

Backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

Port 8000 was occupied by an unrelated service, so 8001 was used.
Repo default remains port 8000 via `py server.py`.

Frontend:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
npm run build
```


## 3. Environment variables, secrets redacted

Backend `backend/.env`, local-only:

```text
APP_NAME=CirrusLabs TalentHub API
ENVIRONMENT=development
API_V1_PREFIX=/api/v1
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=cirruslabs_talenthub
JWT_SECRET_KEY=<redacted-generated-urlsafe-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_URL=http://localhost:5173
ALLOWED_ORIGINS=http://localhost:5173
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
ALLOW_SELF_REGISTRATION=true
REGISTRATION_EMAIL_DOMAIN=cirruslabs.io
BOOTSTRAP_ADMIN_EMAIL=
BOOTSTRAP_ADMIN_PASSWORD=
```

Frontend `frontend/.env.local`, local-only:

```text
VITE_API_BASE_URL=http://localhost:8001/api/v1
```

No VITE secret exists. MongoDB URI and JWT key remain backend-only.
`/api/v1` occurs exactly once: backend mounts api_router at the prefix,
frontend base URL already includes it.

## 4. MongoDB status

- Windows service `MongoDB`: Running, Automatic.
- mongod 8.2.6 at `C:\Program Files\MongoDB\Server\8.2\bin\mongod.exe`.
- Direct PyMongo ping: `{'ok': 1.0}`, PASS.
- Backend `/health`: `ok`, `database_connected true`, PASS.
- Indexes created at startup. No reset, drop, or overwrite performed.
- Limitation: verification wrote one employee user to dev database because no
  isolated test database was configured.

## 5. Files changed

1. `backend/.env`, CREATED locally: runtime settings plus generated JWT secret.
2. `frontend/.env.local`, CREATED locally: API origin with `/api/v1`.
3. `frontend/.env.example`, EDITED: fixed missing `/api/v1` prefix.
4. `frontend/dist/*`: regenerated build output.
5. Dev-database side effect: one verification user in `users`.

## 6. Commands and outcomes

- Python deps import: PASS, `deps-ok`.
- Backend import: PASS, 49 routes, prefix `/api/v1`.
- `pytest -q`: PASS, `4 passed in 0.97s`.
- Mongo ping: PASS.
- `/health`, `/openapi.json`, `/docs`: PASS.
- Register/login/me/jobs/referrals/applications/dashboard: PASS.
- Invalid bearer to admin route: PASS, correctly rejected.
- `npm run build`: PASS twice.
- Frontend dev `/`: PASS HTTP 200.

## 7. Test results

- PASS: backend import/startup.
- PASS: backend unit tests, 4/4.
- PASS: frontend production build.
- PASS: DB-backed auth and workflow reads.
- PASS: auth/role rejection check.
- NOT TESTED: frontend tests, none configured.
- NOT TESTED: destructive workflow tests.
- BLOCKED: isolated test-database run, no test DB configured.
- FAIL: none observed.

## 8. Remaining manual setup

1. Free port 8000 or retain 8001 with aligned frontend URL.
2. Keep local `.env` files private.
3. Remove verification user or use a test database next.
4. Use bootstrap admin variables only for one-time provisioning.
5. Frontend API wiring remains Phase 2 work.

## 9. Phase 1 checklist

- Frontend starts: PASS.
- Backend starts: PASS.
- Database verified: PASS.
- Regression checks: PASS.
- Git initialized: NOT DONE, deferred by approval choice.


No UI, routes, styles, components, mock data, tests, or workflows changed.

Node v24.13.0, npm 11.6.2. pnpm unavailable locally.
