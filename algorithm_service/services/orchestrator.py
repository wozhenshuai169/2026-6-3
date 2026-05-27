"""Tour AI Orchestrator — 统一调度层，根据 intent 路由到下游模块。"""

from algorithm_service.services import (
    decision_router,
    scenic_rag,
    tour_explanation,
    private_assistant,
    vision_recognizer,
    route_recommender,
    memory_extractor,
)


def orchestrate(intent: str, **kwargs) -> dict:
    if intent == "decision":
        return decision_router.evaluate(**kwargs)
    elif intent == "rag":
        return scenic_rag.answer(**kwargs)
    elif intent == "explanation":
        return tour_explanation.generate(**kwargs)
    elif intent == "private_assistant":
        return private_assistant.handle(**kwargs)
    elif intent == "vision":
        return vision_recognizer.recognize(**kwargs)
    elif intent == "route_recommend":
        return route_recommender.recommend(**kwargs)
    elif intent == "memory_extract":
        return memory_extractor.extract(**kwargs)
    else:
        return {"error": f"unknown intent: {intent}"}
