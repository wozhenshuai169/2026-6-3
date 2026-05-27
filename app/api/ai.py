from fastapi import APIRouter, HTTPException

from app.schemas.ai import PublicQuestionRequest, PublicQuestionResponse
from app.services.ai import public_question

router = APIRouter(prefix="/api/ai")


@router.post("/public-question", response_model=PublicQuestionResponse)
async def ask(req: PublicQuestionRequest):
    result = public_question(req.roomId, req.question)
    if result is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    return PublicQuestionResponse(roomId=result["roomId"], answer=result["answer"])
