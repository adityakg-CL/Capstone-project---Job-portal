from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from config.config import get_settings
from middleware.security import hash_password, verify_password, create_access_token
from middleware.dependencies import current_user
from models.database import get_database
from models.schemas.auth import RegisterIn, LoginIn
from models.schemas.domain import PasswordChange
from utils.common import now_utc, audit, public_user_profile

router = APIRouter(prefix="/auth", tags=["authentication"])

# The only identity fields exposed by authentication responses. Everything else
# about the account stays server-side; role and id are read from the token.
def public_user(user):
    profile = public_user_profile(user)
    return {
        "id": profile["id"],
        "full_name": profile["full_name"],
        "email": profile["email"],
        "role": profile["role"],
        "title": profile["title"],
        "team": profile["team"],
        "location": profile["location"],
        "skills": profile["skills"],
        "phone": profile["phone"],
        "avatar": profile["avatar"],
    }


@router.post("/register", status_code=201)
def register(payload: RegisterIn, request: Request):
    settings = get_settings()
    if not settings.allow_self_registration:
        raise HTTPException(403, "Self-registration is disabled")
    email = str(payload.email).lower().strip()
    if settings.registration_email_domain and email.rsplit("@", 1)[-1] != settings.registration_email_domain.lower():
        raise HTTPException(422, f"Use your @{settings.registration_email_domain} work email")
    db = get_database()
    user = {"full_name": payload.full_name.strip(), "email": email, "email_normalized": email,
            "password_hash": hash_password(payload.password), "role": "employee",
            "title": None, "team": None, "location": None, "phone": None, "skills": [],
            "is_active": True, "token_version": 0, "created_at": now_utc(), "updated_at": now_utc()}
    try:
        result = db.users.insert_one(user)
    except DuplicateKeyError:
        raise HTTPException(409, "An account with this email already exists")
    user["_id"] = result.inserted_id
    audit(db, str(result.inserted_id), "auth.register", "user", result.inserted_id)
    return {"user": public_user(user)}

@router.post("/login")
def login(payload: LoginIn, request: Request, response: Response):
    db = get_database()
    email = str(payload.email).lower().strip()
    user = db.users.find_one({"email_normalized": email})
    if not user or not user.get("is_active", True) or not verify_password(payload.password, user.get("password_hash", "")):
        audit(db, user and str(user["_id"]) or None, "auth.login", "user", user and user["_id"], "failure")
        raise HTTPException(401, "Invalid email or password")
    token = create_access_token(str(user["_id"]), user["role"], user.get("token_version", 0))
    settings = get_settings()
    response.set_cookie("access_token", token, httponly=True, secure=settings.cookie_secure,
                        samesite=settings.cookie_samesite, max_age=settings.access_token_expire_minutes * 60,
                        path="/")
    audit(db, str(user["_id"]), "auth.login", "user", user["_id"])
    return {"access_token": token, "token_type": "bearer", "user": public_user(user)}

@router.post("/logout")
def logout(response: Response, user=Depends(current_user)):
    db = get_database()
    db.users.update_one({"_id": ObjectId(user["id"])}, {"$inc": {"token_version": 1}, "$set": {"updated_at": now_utc()}})
    response.delete_cookie("access_token", path="/")
    audit(db, user["id"], "auth.logout", "user", user["id"])
    return {"message": "Logged out"}

@router.get("/me")
def me(user=Depends(current_user)):
    # The authenticated account is resolved from the verified token, never from
    # a client-supplied id, so the UI cannot choose whose identity it displays.
    return {"user": public_user(user)}

@router.post("/change-password")
def change_password(payload: PasswordChange, user=Depends(current_user)):
    if payload.new_password != payload.confirm_password:
        raise HTTPException(422, "New password and confirmation do not match")
    if not verify_password(payload.current_password, user.get("password_hash", "")):
        audit(get_database(), user["id"], "auth.password.change", "user", user["id"], "failure")
        raise HTTPException(400, "Current password is incorrect")
    if payload.new_password == payload.current_password:
        raise HTTPException(422, "Choose a new password different from your current one")
    db = get_database()
    db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {"password_hash": hash_password(payload.new_password), "updated_at": now_utc()},
         "$inc": {"token_version": 1}},
    )
    # Invalidate every existing session for this account, then mint a fresh one
    # so the user who just changed their password stays signed in.
    updated = db.users.find_one({"_id": ObjectId(user["id"])})
    token = create_access_token(user["id"], updated["role"], updated.get("token_version", 0))
    audit(db, user["id"], "auth.password.change", "user", user["id"])
    return {"message": "Password updated", "access_token": token, "token_type": "bearer",
            "user": public_user(updated)}


@router.post("/refresh")
def refresh():
    raise HTTPException(501, "Refresh tokens are not enabled; sign in again after access-token expiry")
