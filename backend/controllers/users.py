from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from pathlib import Path
from config.config import get_settings
from middleware.dependencies import current_user, require_roles
from middleware.security import hash_password, verify_password
from models.database import get_database
from models.schemas.domain import ProfileUpdate, PasswordChange
from utils.common import (
    now_utc,
    serialize,
    audit,
    public_resume_metadata,
    safe_resume_filename,
    new_resume_storage_name,
    resolve_resume_storage,
    is_pdf_bytes,
    detect_image_content_type,
    public_avatar_metadata,
    public_user_profile,
    user_directory,
    new_avatar_storage_name,
    resolve_avatar_storage,
    avatar_file_for_user,
)

router = APIRouter(tags=["users"])

RESUME_CONTENT_TYPE = "application/pdf"



def _resume_response(user_doc: dict) -> dict:
    profile = {k: user_doc.get(k) for k in ("id", "full_name", "email", "role", "title", "team", "location", "skills", "created_at")}
    profile["resume"] = public_resume_metadata(user_doc.get("resume"))
    return {"user": profile}


def _load_user_or_404(db, user_id: str) -> dict:
    if not ObjectId.is_valid(user_id):
        raise HTTPException(404, "User not found")
    user_doc = db.users.find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        raise HTTPException(404, "User not found")
    user_doc["id"] = str(user_doc.pop("_id"))
    return user_doc


def _resume_file_for_user(storage: Path, user_doc: dict) -> Path:
    resume = user_doc.get("resume") or {}
    storage_name = resume.get("storage_name")
    if not storage_name or "/" in storage_name or "\\" in storage_name:
        raise HTTPException(404, "Resume not found")
    candidate = (storage / storage_name).resolve()
    try:
        candidate.relative_to(storage.resolve())
    except ValueError:
        raise HTTPException(404, "Resume not found")
    if not candidate.is_file():
        raise HTTPException(404, "Resume file is missing")
    return candidate


def _can_manager_access_resume(db, manager_id: str, employee_id: str) -> bool:
    applications = db.applications.find({"employee_id": employee_id}, {"job_id": 1})
    job_ids = [a.get("job_id") for a in applications if a.get("job_id") and ObjectId.is_valid(a.get("job_id"))]
    if not job_ids:
        return False
    return db.jobs.count_documents({"_id": {"$in": [ObjectId(j) for j in job_ids]}, "owner_id": manager_id}) > 0


@router.post("/users/me/resume")
async def upload_own_resume(file: UploadFile = File(...), user=Depends(current_user)):
    settings = get_settings()
    if user.get("role") != "employee":
        raise HTTPException(403, "Only employees can manage a profile resume")
    filename = (file.filename or "").strip()
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(422, "Only PDF resumes are accepted")
    data = await file.read()
    if not data:
        raise HTTPException(422, "Resume file is empty")
    if len(data) > settings.resume_max_size_bytes:
        raise HTTPException(413, "Resume exceeds the configured size limit")
    if not is_pdf_bytes(data):
        raise HTTPException(422, "Uploaded file is not a valid PDF resume")
    storage = resolve_resume_storage(settings.resume_storage_dir)
    db = get_database()
    current = db.users.find_one({"_id": ObjectId(user["id"])}, {"resume": 1})
    old_name = (current or {}).get("resume", {}).get("storage_name") if current else None
    storage_name = new_resume_storage_name()
    target = storage / storage_name
    try:
        tmp = target.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(target)
    except OSError:
        raise HTTPException(500, "Could not store the resume; please retry")
    metadata = {
        "storage_name": storage_name,
        "filename": safe_resume_filename(filename),
        "content_type": RESUME_CONTENT_TYPE,
        "size_bytes": len(data),
        "uploaded_at": now_utc(),
    }
    updated = db.users.find_one_and_update(
        {"_id": ObjectId(user["id"])},
        {"$set": {"resume": metadata, "updated_at": now_utc()}},
        return_document=True,
    )
    if updated is None:
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        raise HTTPException(500, "Could not save resume metadata; please retry")
    if old_name and old_name != storage_name:
        try:
            (storage / old_name).unlink(missing_ok=True)
        except OSError:
            pass
    audit(db, user["id"], "user.resume.upload", "user", user["id"])
    return _resume_response({**updated, "id": str(updated.pop("_id"))})


@router.get("/users/me/resume")
def resume_metadata(user=Depends(current_user)):
    db = get_database()
    user_doc = _load_user_or_404(db, user["id"])
    resume = public_resume_metadata(user_doc.get("resume"))
    if not resume:
        raise HTTPException(404, "No resume found")
    return {"resume": resume}


@router.get("/users/me/resume/download")
def download_own_resume(user=Depends(current_user)):
    settings = get_settings()
    db = get_database()
    user_doc = _load_user_or_404(db, user["id"])
    if not user_doc.get("resume"):
        raise HTTPException(404, "No resume found")
    storage = resolve_resume_storage(settings.resume_storage_dir)
    path = _resume_file_for_user(storage, user_doc)
    filename = user_doc["resume"].get("filename") or "resume.pdf"
    return FileResponse(path, media_type=RESUME_CONTENT_TYPE, filename=filename)


@router.delete("/users/me/resume")
def delete_own_resume(user=Depends(current_user)):
    if user.get("role") != "employee":
        raise HTTPException(403, "Only employees can manage a profile resume")
    settings = get_settings()
    db = get_database()
    user_doc = _load_user_or_404(db, user["id"])
    resume = user_doc.get("resume")
    if not resume:
        raise HTTPException(404, "No resume found")
    result = db.users.update_one(
        {"_id": ObjectId(user["id"]), "resume.storage_name": resume.get("storage_name")},
        {"$unset": {"resume": ""}, "$set": {"updated_at": now_utc()}},
    )
    if not result.modified_count:
        raise HTTPException(409, "Resume changed; refresh and retry")
    storage = resolve_resume_storage(settings.resume_storage_dir)
    storage_name = resume.get("storage_name") or ""
    if storage_name and "/" not in storage_name and "\\" not in storage_name:
        try:
            (storage / storage_name).unlink(missing_ok=True)
        except OSError:
            pass
    audit(db, user["id"], "user.resume.delete", "user", user["id"])
    return {"message": "Resume removed"}


@router.get("/users/{user_id}/resume/download")
def download_applicant_resume(user_id: str, user=Depends(require_roles("hiring_manager", "hr_admin"))):
    settings = get_settings()
    db = get_database()
    target = _load_user_or_404(db, user_id)
    if not target.get("resume"):
        raise HTTPException(404, "No resume found")
    if user["role"] != "hr_admin" and not _can_manager_access_resume(db, user["id"], target["id"]):
        raise HTTPException(403, "Forbidden")
    storage = resolve_resume_storage(settings.resume_storage_dir)
    path = _resume_file_for_user(storage, target)
    filename = target["resume"].get("filename") or "resume.pdf"
    audit(db, user["id"], "user.resume.download", "user", user_id)
    return FileResponse(path, media_type=RESUME_CONTENT_TYPE, filename=filename)


@router.get("/users/me")
def get_profile(user=Depends(current_user)):
    db = get_database()
    user_doc = _load_user_or_404(db, user["id"])
    return {"user": public_user_profile(user_doc)}

@router.patch("/users/me")
def update_profile(payload: ProfileUpdate, user=Depends(current_user)):
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(400, "No profile fields supplied")
    db = get_database()
    if "email" in changes:
        email = str(changes["email"]).lower().strip()
        clash = db.users.find_one({"email_normalized": email, "_id": {"$ne": ObjectId(user["id"])}})
        if clash:
            raise HTTPException(409, "Another account already uses this email")
        changes["email"] = email
        changes["email_normalized"] = email
    if "skills" in changes:
        changes["skills"] = [s.strip() for s in (changes["skills"] or []) if str(s).strip()]
    db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": {**changes, "updated_at": now_utc()}})
    audit(db, user["id"], "user.profile.update", "user", user["id"], changes={k: True for k in changes})
    updated = db.users.find_one({"_id": ObjectId(user["id"])})
    # Only allowlisted profile fields are ever written, so role, is_active and
    # token_version are untouched even if a client sends them.
    return {"user": public_user_profile(updated)}

@router.post("/users/me/change-password")
def change_password(payload: PasswordChange, user=Depends(current_user)):
    if payload.new_password != payload.confirm_password:
        raise HTTPException(422, "New password and confirmation do not match")
    if not verify_password(payload.current_password, user.get("password_hash", "")):
        audit(get_database(), user["id"], "user.password.change", "user", user["id"], "failure")
        raise HTTPException(400, "Current password is incorrect")
    if payload.new_password == payload.current_password:
        raise HTTPException(422, "Choose a new password different from your current one")
    db = get_database()
    db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {"password_hash": hash_password(payload.new_password), "updated_at": now_utc()},
         "$inc": {"token_version": 1}},
    )
    updated = db.users.find_one({"_id": ObjectId(user["id"])})
    audit(db, user["id"], "user.password.change", "user", user["id"])
    return {"message": "Password updated", "user": public_user_profile(updated)}


@router.post("/users/me/avatar")
async def upload_own_avatar(file: UploadFile = File(...), user=Depends(current_user)):
    settings = get_settings()
    data = await file.read()
    if not data:
        raise HTTPException(422, "Image file is empty")
    if len(data) > settings.avatar_max_size_bytes:
        raise HTTPException(413, "Image exceeds the configured size limit")
    # Validate the real content type from the bytes, never the browser label.
    content_type = detect_image_content_type(data)
    if content_type is None or content_type not in settings.avatar_content_types:
        raise HTTPException(422, "Only JPEG, PNG or WebP images are accepted")
    storage = resolve_avatar_storage(settings.avatar_storage_dir)
    db = get_database()
    current = db.users.find_one({"_id": ObjectId(user["id"])}, {"avatar": 1})
    old_name = (current or {}).get("avatar", {}).get("storage_name") if current else None
    storage_name = new_avatar_storage_name(content_type)
    target = storage / storage_name
    try:
        tmp = target.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(target)
    except OSError:
        raise HTTPException(500, "Could not store the image; please retry")
    metadata = {
        "storage_name": storage_name,
        "filename": safe_resume_filename(file.filename),
        "content_type": content_type,
        "size_bytes": len(data),
        "uploaded_at": now_utc(),
    }
    updated = db.users.find_one_and_update(
        {"_id": ObjectId(user["id"])},
        {"$set": {"avatar": metadata, "updated_at": now_utc()}},
        return_document=True,
    )
    if updated is None:
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        raise HTTPException(500, "Could not save the image; please retry")
    if old_name and old_name != storage_name:
        try:
            (storage / old_name).unlink(missing_ok=True)
        except OSError:
            pass
    audit(db, user["id"], "user.avatar.upload", "user", user["id"])
    return {"user": public_user_profile(updated)}

@router.delete("/users/me/avatar")
def delete_own_avatar(user=Depends(current_user)):
    settings = get_settings()
    db = get_database()
    current = db.users.find_one({"_id": ObjectId(user["id"])}, {"avatar": 1})
    storage_name = (current or {}).get("avatar", {}).get("storage_name") if current else None
    if not storage_name:
        raise HTTPException(404, "No profile photo found")
    result = db.users.update_one(
        {"_id": ObjectId(user["id"]), "avatar.storage_name": storage_name},
        {"$unset": {"avatar": ""}, "$set": {"updated_at": now_utc()}},
    )
    if not result.modified_count:
        raise HTTPException(409, "Photo changed; refresh and retry")
    if storage_name and "/" not in storage_name and "\\" not in storage_name:
        try:
            (resolve_avatar_storage(settings.avatar_storage_dir) / storage_name).unlink(missing_ok=True)
        except OSError:
            pass
    audit(db, user["id"], "user.avatar.delete", "user", user["id"])
    return {"message": "Profile photo removed"}

@router.get("/users/me/avatar")
def own_avatar_metadata(user=Depends(current_user)):
    db = get_database()
    user_doc = _load_user_or_404(db, user["id"])
    avatar = public_avatar_metadata(user_doc.get("avatar"))
    if not avatar:
        raise HTTPException(404, "No profile photo found")
    return {"avatar": avatar}

@router.get("/users/{user_id}/avatar")
def download_avatar(user_id: str, user=Depends(current_user)):
    """Serve a profile photo.

    Managers/HR may read the photo of someone who applied to a job they own, so
    applicant rows can show a real avatar instead of a fabricated one.
    """
    settings = get_settings()
    db = get_database()
    target = _load_user_or_404(db, user_id)
    if user["role"] == "hiring_manager" and target["id"] != user["id"]:
        if not _can_manager_access_resume(db, user["id"], target["id"]):
            raise HTTPException(403, "Forbidden")
    elif user["role"] == "employee" and target["id"] != user["id"]:
        raise HTTPException(403, "Forbidden")
    if not target.get("avatar"):
        raise HTTPException(404, "No profile photo found")
    try:
        path = avatar_file_for_user(resolve_avatar_storage(settings.avatar_storage_dir), target)
    except ValueError:
        raise HTTPException(404, "Profile photo is missing")
    return FileResponse(path, media_type=target["avatar"].get("content_type") or "application/octet-stream",
                        filename=target["avatar"].get("filename") or "avatar")

@router.get("/admin/applicants/{employee_id}")
def applicant_directory_entry(employee_id: str, user=Depends(require_roles("hiring_manager", "hr_admin"))):
    """Display identity for an applicant so manager views never fabricate a name.

    hr_admin may read any applicant; a hiring_manager only for people who
    applied to a job they own.
    """
    db = get_database()
    target = _load_user_or_404(db, employee_id)
    if user["role"] != "hr_admin" and not _can_manager_access_resume(db, user["id"], target["id"]):
        raise HTTPException(403, "Forbidden")
    profile = public_user_profile(target)
    return {"applicant": {
        "id": profile["id"],
        "full_name": profile["full_name"],
        "email": profile["email"],
        "title": profile["title"],
        "team": profile["team"],
        "location": profile["location"],
        "has_resume": bool(profile["resume"]),
    }}


@router.get("/admin/users", dependencies=[Depends(require_roles("hr_admin"))])
def list_users(page: int = 1, page_size: int = 20, role: str | None = None, user=Depends(current_user)):
    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(422, "Invalid pagination")
    db = get_database()
    query = {"role": role} if role else {}
    total = db.users.count_documents(query)
    items = [serialize({k:v for k,v in d.items() if k != "password_hash"}) for d in db.users.find(query).skip((page-1)*page_size).limit(page_size)]
    return {"items": items, "page": page, "page_size": page_size, "total": total}

@router.patch("/admin/users/{user_id}/role", dependencies=[Depends(require_roles("hr_admin"))])
def change_role(user_id: str, role: str, user=Depends(current_user)):
    if role not in {"employee", "hiring_manager", "hr_admin"}:
        raise HTTPException(422, "Invalid role")
    if not ObjectId.is_valid(user_id):
        raise HTTPException(404, "User not found")
    db = get_database()
    target = db.users.find_one({"_id": ObjectId(user_id)})
    if not target:
        raise HTTPException(404, "User not found")
    if target["_id"] == ObjectId(user["id"]) and role != "hr_admin":
        raise HTTPException(400, "You cannot remove your own HR/Admin role")
    db.users.update_one({"_id": target["_id"]}, {"$set": {"role": role, "updated_at": now_utc()}, "$inc": {"token_version": 1}})
    audit(db, user["id"], "user.role.change", "user", user_id, changes={"role": role})
    return {"message": "Role updated; the target user must sign in again"}
