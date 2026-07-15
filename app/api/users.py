from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.core.auth import get_bearer_token, get_current_user, require_room_member
from app.core.rate_limit import enforce_rate_limit
from app.schemas.users import (
    AuthResponse,
    CurrentUserResponse,
    GuestRequest,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    WsTicketRequest,
    WsTicketResponse,
)
from app.services.stats import record_event
from app.services.users import (
    create_guest_session,
    create_ws_ticket,
    login_user,
    register_user,
    revoke_token,
)

router = APIRouter(prefix="/api/auth")


@router.post("/register", response_model=RegisterResponse)
async def register(req: RegisterRequest, request: Request):
    enforce_rate_limit("auth", request.client.host if request.client else "unknown", 10, 60)
    try:
        user = register_user(req.userName, req.password, req.role)
    except KeyError:
        raise HTTPException(status_code=409, detail="User name already exists") from None
    record_event("register", success=True, payload={"userId": user["userId"]})
    return RegisterResponse(**user)


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, request: Request):
    enforce_rate_limit("auth", request.client.host if request.client else "unknown", 10, 60)
    user = login_user(req.userName, req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid user name or password")
    record_event("login", success=True, payload={"userId": user["userId"]})
    return AuthResponse(**user)


@router.post("/logout", status_code=204)
async def logout(token: str = Depends(get_bearer_token)):
    revoke_token(token)
    return Response(status_code=204)


@router.get("/me", response_model=CurrentUserResponse)
async def current_user(user: dict = Depends(get_current_user)):
    return CurrentUserResponse(**user)


@router.post("/guest", response_model=AuthResponse)
async def guest(req: GuestRequest, request: Request):
    enforce_rate_limit("auth", request.client.host if request.client else "unknown", 10, 60)
    return AuthResponse(**create_guest_session(req.displayName, req.role))


@router.post("/ws-ticket", response_model=WsTicketResponse)
async def websocket_ticket(req: WsTicketRequest, user: dict = Depends(get_current_user)):
    require_room_member(req.roomId, user)
    return WsTicketResponse(**create_ws_ticket(user["userId"], req.roomId))
