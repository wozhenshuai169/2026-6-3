from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.auth import get_bearer_token, get_current_user
from app.schemas.users import (
    AuthResponse,
    CurrentUserResponse,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
)
from app.services.stats import record_event
from app.services.users import login_user, register_user, revoke_token

router = APIRouter(prefix="/api/auth")


@router.post("/register", response_model=RegisterResponse)
async def register(req: RegisterRequest):
    try:
        user = register_user(req.userName, req.password, req.role)
    except KeyError:
        raise HTTPException(status_code=409, detail="User name already exists") from None
    record_event("register", success=True, payload={"userId": user["userId"]})
    return RegisterResponse(**user)


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
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
