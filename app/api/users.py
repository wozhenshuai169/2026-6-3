from fastapi import APIRouter

from app.schemas.users import RegisterRequest, RegisterResponse
from app.services.users import register_user
from app.services.stats import record_event

router = APIRouter(prefix="/api/auth")


@router.post("/register", response_model=RegisterResponse)
async def register(req: RegisterRequest):
    user = register_user(req.userName, req.password)
    record_event("register", success=True, payload={"userId": user["userId"]})
    return RegisterResponse(
        userId=user["userId"],
        userName=user["userName"],
        token=user["token"],
    )
