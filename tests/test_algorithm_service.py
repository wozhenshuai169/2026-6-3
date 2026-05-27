from ai_algorithm_service.evaluation import EvaluationHarness
from ai_algorithm_service.orchestrator import TourAIOrchestrator
from ai_algorithm_service.schemas import AlgorithmRequest, TouristProfile


def test_public_question_interrupts_and_returns_citations():
    response = TourAIOrchestrator().handle(AlgorithmRequest(channel="public", text="主展厅是什么时候建的？"))
    assert response.decision.decision == "interrupt_and_answer"
    assert response.decision.channel == "public"
    assert response.citations
    assert response.stateUpdate["shouldResume"] is True
    assert "resumeText" in response.stateUpdate


def test_private_need_is_not_broadcast():
    response = TourAIOrchestrator().handle(AlgorithmRequest(channel="public", text="厕所在哪里？"))
    assert response.decision.decision == "private_reply"
    assert response.decision.channel == "private"
    assert response.private is not None
    assert response.answer


def test_emergency_escalates_to_leader():
    response = TourAIOrchestrator().handle(AlgorithmRequest(channel="private", text="我找不到队伍了"))
    assert response.decision.decision == "emergency_alert"
    assert response.decision.needLeaderNotify is True
    assert response.decision.riskLevel == "high"
    assert response.private and response.private.leaderMessage


def test_unknown_rag_does_not_fabricate():
    response = TourAIOrchestrator().handle(AlgorithmRequest(channel="public", text="这里有没有恐龙化石？"))
    assert "没有查到可靠信息" in (response.answer or "")
    assert response.citations == []


def test_vision_uses_rag_when_object_recognized():
    response = TourAIOrchestrator().handle(
        AlgorithmRequest(channel="public", text="介绍这张图", imageUrl="bell_tower_photo.jpg")
    )
    assert response.vision is not None
    assert response.vision.recognizedObject == "钟楼"
    assert response.citations


def test_route_recommendation_uses_memory_tags():
    request = AlgorithmRequest(
        channel="private",
        text="推荐路线",
        profile=TouristProfile(memoryTags={"stamina": "low", "companions": ["elderly"]}),
    )
    response = TourAIOrchestrator().recommend_routes(request)
    assert response.routes[0].routeId == "short"


def test_memory_extracts_tags_without_raw_text():
    tags = TourAIOrchestrator().extract_memory(AlgorithmRequest(text="老人走不动，想少走路"))
    assert tags["stamina"] == "low"
    assert "elderly" in tags["companions"]
    assert "rawText" not in tags


def test_evaluation_harness_covers_spec_metrics():
    metrics = EvaluationHarness().run()
    assert metrics["caseCount"] >= 30
    assert metrics["privateLeakCount"] == 0
    assert metrics["riskEscalationRecall"] == 1.0
    assert metrics["under10sRate"] == 1.0

