from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError
from config.config import get_settings
from models.database import connect, close, get_database
from models.indexes import ensure_indexes, migrate_job_statuses
from routes.router import api_router

settings = get_settings()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        connect()
        ensure_indexes()
        migrate_job_statuses(get_database())
        # Optional one-time bootstrap: only when both credentials are explicitly configured.
        if settings.bootstrap_admin_email and settings.bootstrap_admin_password:
            from middleware.security import hash_password
            from utils.common import now_utc
            email = settings.bootstrap_admin_email.lower().strip()
            db = get_database()
            if not db.users.find_one({"email_normalized": email}):
                db.users.insert_one({"full_name": "Initial HR Admin", "email": email, "email_normalized": email,
                    "password_hash": hash_password(settings.bootstrap_admin_password), "role": "hr_admin",
                    "is_active": True, "token_version": 0, "created_at": now_utc(), "updated_at": now_utc(),
                    "title": "HR Admin", "team": "People & Culture", "skills": []})
        app.state.database_ready = True
    except PyMongoError as exc:
        app.state.database_ready = False
        app.state.database_error = str(exc)
        logger.exception("MongoDB is unavailable during application startup")
    yield
    close()

app = FastAPI(title=settings.app_name, version="1.0.0", description="Internal hiring and employee referral API. No SSO/OAuth.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
                   allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"], allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"])
app.include_router(api_router, prefix=settings.api_v1_prefix)

@app.exception_handler(PyMongoError)
async def handle_database_error(request: Request, exc: PyMongoError):
    logger.error("MongoDB operation failed for %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(status_code=503, content={"detail": "Database is temporarily unavailable"})

@app.get("/health")
def health():
    ready = bool(getattr(app.state, "database_ready", False))
    return JSONResponse(status_code=200 if ready else 503, content={"status": "ok" if ready else "degraded", "database_connected": ready})

@app.get("/")
def root():
    return {"name": settings.app_name, "docs": "/docs", "openapi": "/openapi.json"}
