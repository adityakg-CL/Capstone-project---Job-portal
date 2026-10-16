# CirrusLabs TalentHub API

Separate FastAPI backend for the existing React/Vite frontend. Uses Python, FastAPI, PyMongo and MongoDB. Email/password + JWT only; no SSO, Microsoft Entra ID, OAuth or OIDC.

## Prerequisites
- Python 3.11+
- MongoDB instance
- Node frontend separately, when integrating

## Setup (Windows PowerShell)
```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env`; replace `JWT_SECRET_KEY` with a long random secret and configure `MONGODB_URI`, `MONGODB_DATABASE`, `ALLOWED_ORIGINS`. Start MongoDB, then:
```powershell
uvicorn main:app --reload
# or: py server.py
```
Open `http://localhost:8000/docs` and `http://localhost:8000/health`.

## Bootstrap HR Admin
For a one-time initial admin, set `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` in `.env` before starting. If no account with that normalized email exists, startup inserts it with `hr_admin` role. Remove these variables after provisioning. Keep `.env` private. Self-registration, when enabled, can only create employee accounts.

## Frontend connection
Set `VITE_API_BASE_URL=http://localhost:8000/api/v1` in the frontend `.env.local`. Current frontend is still demo/local-state based and needs API calls wired in separately. When using cookie auth across origins, configure credentials in the frontend HTTP client and implement CSRF protection for production. Bearer auth can use the returned `access_token`.

## Tests
```powershell
pytest -q
```
Database-backed tests need a separate isolated test database. Do not claim they passed unless actually run against MongoDB.

## Security / limitations
- No refresh-token flow; expired access token requires login again.
- This version sets an HTTP-only cookie and returns the access token for bearer clients. Cross-site cookie deployments require `COOKIE_SECURE=true` and a CSRF strategy.
- Login throttling is not built into this initial scaffold; enforce at the reverse proxy/API gateway before production.
- Bonus amounts are never assumed; HR must submit an explicit amount.
- `paid` means payment tracking was updated and does not transfer money.
- MongoDB transaction support is not used; the current implementation uses conditional atomic updates for state transitions.
- Run a security review and integration tests before production use.


