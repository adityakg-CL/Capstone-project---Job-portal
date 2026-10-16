from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId
from jwt import PyJWTError
from models.database import get_database
from middleware.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)

def current_user(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)):
    token = credentials.credentials if credentials else request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id or not ObjectId.is_valid(user_id):
            raise ValueError("Invalid subject")
    except (PyJWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")
    user = get_database().users.find_one({"_id": ObjectId(user_id), "is_active": True})
    if not user or user.get("token_version", 0) != payload.get("ver", 0):
        raise HTTPException(status_code=401, detail="Session is no longer valid")
    user["id"] = str(user.pop("_id"))
    return user

def require_roles(*roles: str):
    def dependency(user=Depends(current_user)):
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
        return user
    return dependency
