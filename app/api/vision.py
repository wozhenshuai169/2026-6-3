from fastapi import APIRouter, HTTPException

from app.schemas.vision import VisionRecognizeRequest, VisionRecognizeResponse
from app.services.vision import recognize_image

router = APIRouter(prefix="/api/vision")


@router.post("/recognize", response_model=VisionRecognizeResponse)
async def vision_recognize(req: VisionRecognizeRequest):
    """图片识景：上传图片URL，返回识别到的景点信息"""
    result = await recognize_image(req.roomId, req.userId, req.imageUrl, req.currentSpotId)
    if result is None:
        raise HTTPException(status_code=404, detail="房间不存在")
    return VisionRecognizeResponse(**result)
