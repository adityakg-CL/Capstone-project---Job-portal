from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from bson import ObjectId

def now_utc():
    return datetime.now(timezone.utc)

def serialize(doc):
    if doc is None:
        return None
    result = dict(doc)
    if "_id" in result:
        result["id"] = str(result.pop("_id"))
    for key, value in list(result.items()):
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, list):
            result[key] = [str(v) if isinstance(v, ObjectId) else v for v in value]
    return result

def public_resume_metadata(resume: dict | None) -> dict | None:
    """Return only safe resume metadata; never filesystem paths."""
    if not resume:
        return None
    return {
        "filename": resume.get("filename"),
        "content_type": resume.get("content_type"),
        "size_bytes": resume.get("size_bytes"),
        "uploaded_at": resume.get("uploaded_at"),
    }

def safe_resume_filename(filename: str | None) -> str:
    """Sanitize a browser-supplied filename for display only."""
    name = (filename or "resume.pdf").strip().replace("\\", "/").split("/")[-1]
    name = "".join(ch for ch in name if ch.isalnum() or ch in (" ", ".", "-", "_")).strip()
    return name[:120] or "resume.pdf"

def new_resume_storage_name() -> str:
    return f"{uuid4().hex}.pdf"

def resolve_resume_storage(base_dir: str) -> Path:
    path = Path(base_dir)
    if not path.is_absolute():
        # Resolve relative storage paths against the backend package directory,
        # keeping uploads outside frontend public/static directories.
        path = Path(__file__).resolve().parent.parent / path
    path.mkdir(parents=True, exist_ok=True)
    return path

def is_pdf_bytes(data: bytes) -> bool:
    """Validate the PDF signature instead of trusting browser MIME type."""
    if not data.startswith(b"%PDF-"):
        return False
    # Require a PDF end-of-file marker somewhere in the payload.
    return b"%%EOF" in data


def detect_image_content_type(data: bytes) -> str | None:
    """Sniff the real image type from magic bytes.

    A browser-supplied filename or MIME type is never trusted on its own.
    """
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    # WebP: "RIFF" <4-byte size> "WEBP"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def public_avatar_metadata(avatar: dict | None) -> dict | None:
    """Return only safe avatar metadata; never filesystem paths or storage names."""
    if not avatar:
        return None
    return {
        "filename": avatar.get("filename"),
        "content_type": avatar.get("content_type"),
        "size_bytes": avatar.get("size_bytes"),
        "uploaded_at": avatar.get("uploaded_at"),
    }


def new_avatar_storage_name(content_type: str) -> str:
    extension = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(content_type, "img")
    return f"{uuid4().hex}.{extension}"


def resolve_avatar_storage(base_dir: str) -> Path:
    """Resolve avatar storage against the backend root, outside frontend public/."""
    path = Path(base_dir)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def avatar_file_for_user(storage: Path, user_doc: dict) -> Path:
    """Resolve a stored avatar path with path-traversal protection."""
    avatar = user_doc.get("avatar") or {}
    storage_name = avatar.get("storage_name")
    if not storage_name or "/" in storage_name or "\\" in storage_name:
        raise ValueError("Avatar file is not available")
    candidate = (storage / storage_name).resolve()
    try:
        candidate.relative_to(storage.resolve())
    except ValueError as exc:
        raise ValueError("Avatar file is not available") from exc
    if not candidate.is_file():
        raise ValueError("Avatar file is missing")
    return candidate


# Fields the authenticated user may read/update about themselves.
# "role", "email", "password_hash", "is_active" and "token_version" are
# intentionally excluded so a profile edit can never grant privileges.
PROFILE_FIELDS = ("full_name", "email", "phone", "title", "team", "location", "skills")


def public_user_profile(user: dict) -> dict:
    """Single canonical public representation of an account, shared by every screen."""
    result = {field: user.get(field) for field in PROFILE_FIELDS}
    result["id"] = str(user["_id"]) if user.get("_id") else user.get("id")
    result["role"] = user.get("role")
    result["created_at"] = user.get("created_at")
    result["avatar"] = public_avatar_metadata(user.get("avatar"))
    result["resume"] = public_resume_metadata(user.get("resume")) if user.get("role") == "employee" else None
    return result


def user_directory(db, user_ids) -> dict:
    """Map user ids -> {id, full_name, email, title, team} for display joins.

    Avoids N+1 queries and keeps unknown/legacy ids resolvable as a fallback label.
    """
    ids = []
    for value in user_ids:
        if not value:
            continue
        text = str(value)
        if ObjectId.is_valid(text):
            ids.append(ObjectId(text))
    directory = {}
    if ids:
        for doc in db.users.find(
            {"_id": {"$in": list(dict.fromkeys(ids))}},
            {"full_name": 1, "email": 1, "title": 1, "team": 1},
        ):
            directory[str(doc["_id"])] = {
                "id": str(doc["_id"]),
                "full_name": doc.get("full_name"),
                "email": doc.get("email"),
                "title": doc.get("title"),
                "team": doc.get("team"),
            }
    return directory


def audit(db, actor_id, action, entity_type, entity_id=None, outcome="success", changes=None):
    db.audit_logs.insert_one({
        "actor_id": str(actor_id), "action": action, "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id else None, "outcome": outcome,
        "changes": changes or {}, "created_at": now_utc()
    })

def notify(db, recipient_id, kind, title, message, entity_type=None, entity_id=None):
    if not recipient_id:
        return
    db.notifications.insert_one({
        "recipient_id": str(recipient_id), "type": kind, "title": title,
        "message": message, "entity_type": entity_type, "entity_id": str(entity_id) if entity_id else None,
        "read_at": None, "created_at": now_utc()
    })
