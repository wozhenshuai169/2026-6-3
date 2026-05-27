"""Tour AI Orchestrator HTTP 端点 — 统一响应 {code, message, data}。"""

from fastapi import APIRouter

from algorithm_service.schemas.decision import DecisionRequest, DecisionResponse
from algorithm_service.schemas.rag import ScenicRAGRequest, ScenicRAGResponse
from algorithm_service.schemas.explanation import ExplanationRequest, ExplanationResponse
from algorithm_service.schemas.private_assistant import PrivateAssistantRequest, PrivateAssistantResponse
from algorithm_service.schemas.vision import VisionRequest, VisionResponse
from algorithm_service.schemas.route import RouteRecommendRequest, RouteRecommendResponse
from algorithm_service.schemas.memory import MemoryExtractRequest, MemoryExtractResponse
from algorithm_service.services import (
    decision_router,
    scenic_rag,
    tour_explanation,
    private_assistant,
    vision_recognizer,
    route_recommender,
    memory_extractor,
)

router = APIRouter(prefix="/api/v1")


def _ok(data: dict) -> dict:
    return {"code": 200, "message": "success", "data": data}


# ── DecisionRouter ──

@router.post("/decision")
async def decision(req: DecisionRequest):
    result = decision_router.evaluate(
        roomId=req.roomId, userId=req.userId,
        event=req.event, context=req.context,
    )
    return _ok(DecisionResponse(**result).model_dump())


# ── ScenicRAG ──

@router.post("/rag")
async def rag(req: ScenicRAGRequest):
    result = scenic_rag.answer(
        roomId=req.roomId, userId=req.userId,
        question=req.question, currentSpot=req.currentSpot,
        context=req.context,
    )
    return _ok(ScenicRAGResponse(**result).model_dump())


# ── TourExplanation ──

@router.post("/explanation")
async def explanation(req: ExplanationRequest):
    result = tour_explanation.generate(
        roomId=req.roomId, spotId=req.spotId,
        spotName=req.spotName, style=req.style, context=req.context,
    )
    return _ok(ExplanationResponse(**result).model_dump())


# ── PrivateAssistant ──

@router.post("/private-assistant")
async def private_assist(req: PrivateAssistantRequest):
    result = private_assistant.handle(
        roomId=req.roomId, userId=req.userId,
        question=req.question, context=req.context,
    )
    return _ok(PrivateAssistantResponse(**result).model_dump())


# ── VisionRecognizer ──

@router.post("/vision")
async def vision(req: VisionRequest):
    result = vision_recognizer.recognize(
        roomId=req.roomId, userId=req.userId,
        imageUrl=req.imageUrl, context=req.context,
    )
    return _ok(VisionResponse(**result).model_dump())


# ── RouteRecommender ──

@router.post("/route-recommend")
async def route_recommend(req: RouteRecommendRequest):
    result = route_recommender.recommend(
        roomId=req.roomId, currentSpot=req.currentSpot,
        preferences=req.preferences, context=req.context,
    )
    return _ok(RouteRecommendResponse(**result).model_dump())


# ── MemoryExtractor ──

@router.post("/memory-extract")
async def memory_extract(req: MemoryExtractRequest):
    result = memory_extractor.extract(
        userId=req.userId, dialogue=req.dialogue, context=req.context,
    )
    return _ok(MemoryExtractResponse(**result).model_dump())


# ── Tour AI Orchestrator 统一入口 ──

@router.post("/orchestrate")
async def orchestrate(req: dict):
    intent = req.get("intent", "")
    result = _dispatch(intent, req)
    return _ok(result)


def _dispatch(intent: str, req: dict) -> dict:
    r = req
    if intent == "decision":
        return decision_router.evaluate(
            roomId=r.get("roomId", ""), userId=r.get("userId", ""),
            event=r.get("event", ""), context=r.get("context", {}),
        )
    elif intent == "rag":
        return scenic_rag.answer(
            roomId=r.get("roomId", ""), userId=r.get("userId", ""),
            question=r.get("question", ""), currentSpot=r.get("currentSpot", ""),
            context=r.get("context", {}),
        )
    elif intent == "explanation":
        return tour_explanation.generate(
            roomId=r.get("roomId", ""), spotId=r.get("spotId", ""),
            spotName=r.get("spotName", ""), style=r.get("style", "standard"),
            context=r.get("context", {}),
        )
    elif intent == "private_assistant":
        return private_assistant.handle(
            roomId=r.get("roomId", ""), userId=r.get("userId", ""),
            question=r.get("question", ""), context=r.get("context", {}),
        )
    elif intent == "vision":
        return vision_recognizer.recognize(
            roomId=r.get("roomId", ""), userId=r.get("userId", ""),
            imageUrl=r.get("imageUrl", ""), context=r.get("context", {}),
        )
    elif intent == "route_recommend":
        return route_recommender.recommend(
            roomId=r.get("roomId", ""), currentSpot=r.get("currentSpot", ""),
            preferences=r.get("preferences", []), context=r.get("context", {}),
        )
    elif intent == "memory_extract":
        return memory_extractor.extract(
            userId=r.get("userId", ""), dialogue=r.get("dialogue", ""),
            context=r.get("context", {}),
        )
    else:
        return {"error": f"unknown intent: {intent}"}
