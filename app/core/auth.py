from collections.abc import Callable

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.rooms import get_room
from app.services.users import get_user_by_token

bearer_scheme = HTTPBearer(auto_error=False)


def authenticate_token(token: str | None) -> dict:
    user = get_user_by_token(token or "")
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    return authenticate_token(credentials.credentials if credentials else None)


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    authenticate_token(credentials.credentials)
    return credentials.credentials


def require_roles(*allowed_roles: str) -> Callable:
    def dependency(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return dependency


def require_room_member(room_id: str, user: dict, *, leader_only: bool = False) -> dict:
    room = get_room(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    if user.get("role") == "admin":
        return room
    if leader_only and room.get("leaderId") != user["userId"]:
        raise HTTPException(status_code=403, detail="Only the room leader can perform this action")
    if not any(member["userId"] == user["userId"] for member in room.get("members", [])):
        raise HTTPException(status_code=403, detail="Room membership required")
    return room


def require_matching_user(user_id: str, user: dict) -> None:
    if user.get("role") != "admin" and user_id != user["userId"]:
        raise HTTPException(status_code=403, detail="Cannot act as another user")
