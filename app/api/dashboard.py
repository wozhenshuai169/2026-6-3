from fastapi import APIRouter, Depends

from app.core.auth import require_roles

from app.services.rooms import count_rooms
from app.services.stats import (
    get_hot_questions,
    get_hot_spots,
    get_overview,
    get_satisfaction,
    get_system_metrics,
)
from app.services.users import count_users

router = APIRouter(prefix="/api/dashboard", dependencies=[Depends(require_roles("admin"))])


@router.get("/overview")
async def overview():
    return get_overview(
        active_rooms=count_rooms(active_only=True),
        visitor_count=count_users(today_only=True),
    )


@router.get("/hot-questions")
async def hot_questions():
    return {"items": get_hot_questions()}


@router.get("/hot-spots")
async def hot_spots():
    return {"items": get_hot_spots()}


@router.get("/satisfaction")
async def satisfaction():
    return get_satisfaction()


@router.get("/system-metrics")
async def system_metrics():
    return get_system_metrics()
