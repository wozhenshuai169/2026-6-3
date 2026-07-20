from fastapi import APIRouter, Depends

from app.core.auth import get_current_user, require_roles
from app.core.errors import AppError
from app.schemas.operation_events import CreateOperationEventRequest, OperationEventResponse, UpdateOperationEventRequest
from app.services.operation_events import create_operation_event, list_operation_events, update_operation_event_status

router = APIRouter(prefix="/api/operation-events")


@router.get("", response_model=list[OperationEventResponse])
async def list_events(scenicAreaId: str, user: dict = Depends(get_current_user)):
    del user
    return list_operation_events(scenicAreaId)


@router.post("", response_model=OperationEventResponse)
async def create_event(req: CreateOperationEventRequest, admin: dict = Depends(require_roles("admin"))):
    return create_operation_event(req.model_dump(), admin["userId"])


@router.patch("/{event_id}", response_model=OperationEventResponse)
async def update_event(event_id: str, req: UpdateOperationEventRequest, admin: dict = Depends(require_roles("admin"))):
    del admin
    result = update_operation_event_status(event_id, req.status)
    if result is None:
        raise AppError(404, "OPERATION_EVENT_NOT_FOUND", "运营事件不存在")
    return result
