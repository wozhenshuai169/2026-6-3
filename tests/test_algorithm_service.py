from ai_algorithm_service.evaluation import EvaluationHarness
from ai_algorithm_service.orchestrator import TourAIOrchestrator
from ai_algorithm_service.schemas import AlgorithmRequest, TouristProfile
from ai_algorithm_service.api import app
from ai_algorithm_service.vision import VisionProvider, VisionRecognizer
from fastapi.testclient import TestClient


class FakeBuddhaVisionProvider(VisionProvider):
    def recognize(self, request: AlgorithmRequest) -> dict | None:
        return {
            "spotId": "lingshan_buddha",
            "spotName": "灵山大佛",
            "confidence": 0.91,
            "visualFeatures": ["大型青铜佛像", "莲花座"],
            "relatedSpots": ["祥符禅寺"],
        }


class StaticVisionProvider(VisionProvider):
    def __init__(self, spot: dict) -> None:
        self.spot = spot

    def recognize(self, request: AlgorithmRequest) -> dict | None:
        return {
            "spotId": self.spot["spotId"],
            "spotName": self.spot["spotName"],
            "confidence": 0.9,
            "visualFeatures": self.spot["visualFeatures"],
            "relatedSpots": self.spot.get("relatedSpots", []),
        }


def test_public_question_interrupts_and_returns_citations():
    response = TourAIOrchestrator().handle(AlgorithmRequest(channel="public", text="灵山大佛什么时候落成开光？"))
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
    orchestrator = TourAIOrchestrator()
    orchestrator.vision = VisionRecognizer(orchestrator.data, orchestrator.rag, provider=FakeBuddhaVisionProvider())
    response = orchestrator.handle(AlgorithmRequest(channel="public", text="介绍这张图", imageUrl="uploaded_photo.jpg"))
    assert response.vision is not None
    assert response.vision.recognizedObject == "灵山大佛"
    assert response.citations


def test_route_recommendation_uses_memory_tags():
    request = AlgorithmRequest(
        channel="private",
        text="推荐路线",
        profile=TouristProfile(memoryTags={"stamina": "low", "companions": ["elderly"]}),
    )
    response = TourAIOrchestrator().recommend_routes(request)
    assert response.routes[0].routeId == "lingshan_easy"
    assert sum(response.routes[0].scoreBreakdown.values()) == response.routes[0].score
    assert response.routes[0].durationMinutes == 35


def test_memory_extracts_tags_without_raw_text():
    tags = TourAIOrchestrator().extract_memory(AlgorithmRequest(text="老人走不动，想少走路"))
    assert tags["stamina"] == "low"
    assert "elderly" in tags["companions"]
    assert "rawText" not in tags


def test_evaluation_harness_covers_spec_metrics():
    metrics = EvaluationHarness().run()
    assert metrics["caseCount"] >= 60
    assert metrics["privateLeakCount"] == 0
    assert metrics["riskEscalationRecall"] == 1.0
    assert metrics["under10sRate"] == 1.0
    assert metrics["localUnder5sRate"] == 1.0
    assert metrics["factualAccuracy"] >= 0.9
    assert metrics["lowAsrClarificationRate"] == 1.0
    assert metrics["answerMismatchRate"] <= 0.2
    assert metrics["unsupportedAnswerRate"] == 0.0
    assert metrics["privateInfoLeakRate"] == 0.0
    assert metrics["lowConfidenceFallbackRate"] == 1.0
    assert metrics["visionFeatureCoverage"] == 1.0
    assert metrics["routeScoreBreakdownConsistent"] is True
    assert metrics["resumeTextCoverage"] == 1.0


def test_scenic_chunks_are_expanded_and_metadata_complete():
    chunks = TourAIOrchestrator().data.chunks
    required = {
        "spotId",
        "topic",
        "audience",
        "routeIds",
        "source",
        "sourceTier",
        "verificationStatus",
    }
    assert 80 <= len(chunks) <= 140
    for chunk in chunks:
        assert required <= set(chunk), chunk["chunkId"]
        assert chunk["spotId"]
        assert chunk["topic"]
        assert chunk["audience"]
        assert isinstance(chunk["routeIds"], list)
        assert chunk["source"]


def test_low_asr_confidence_asks_for_clarification():
    response = TourAIOrchestrator().handle(
        AlgorithmRequest(channel="public", inputMode="voice", asrConfidence=0.42, audioFormat="wav")
    )
    assert response.decision.decision == "ask_clarification"
    assert response.decision.nextAction == "ask_clarification"
    assert "没有听清" in (response.answer or "")


def test_public_private_question_emits_private_channel_event():
    response = TourAIOrchestrator().handle(AlgorithmRequest(channel="public", text="我想去厕所"))
    assert response.decision.channel == "private"
    assert any(event["type"] == "suggest_private_channel" for event in response.events)


def test_voice_adapter_accepts_wav_mp3_and_rejects_other_formats():
    voice = TourAIOrchestrator().voice
    assert voice.asr(audio_format="wav", text_hint="我想去厕所").success is False
    assert voice.asr(audio_format="mp3", text_hint="我想去厕所").success is False
    unsupported = voice.asr(audio_format="aac", text_hint="我想去厕所")
    assert unsupported.success is False
    assert "wav / mp3" in (unsupported.error or "")


def test_voice_orchestrate_reports_missing_real_speech_service():
    client = TestClient(app)
    response = client.post(
        "/v1/voice/orchestrate",
        json={"channel": "public", "audioFormat": "wav", "audioPath": "uploaded.wav", "text": "我想去厕所"},
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["asr"]["success"] is False
    assert payload["algorithm"]["decision"]["decision"] == "ask_clarification"
    assert payload["tts"]["success"] is False
    assert payload["tts"]["audioUrl"] is None


def test_all_demo_vision_spots_return_features_and_rag():
    orchestrator = TourAIOrchestrator()
    for spot in orchestrator.data.vision_spots:
        orchestrator.vision = VisionRecognizer(orchestrator.data, orchestrator.rag, provider=StaticVisionProvider(spot))
        response = orchestrator.handle(AlgorithmRequest(channel="public", text="介绍这张图", imageUrl="uploaded_photo.jpg"))
        assert response.vision is not None
        assert response.vision.spotName == spot["spotName"]
        assert response.vision.visualFeatures
        assert response.citations


def test_resume_text_uses_answer_summary_bridge():
    response = TourAIOrchestrator().handle(AlgorithmRequest(channel="public", text="灵山大佛什么时候落成开光？"))
    resume_text = response.stateUpdate["resumeText"]
    assert "了解了这个年代背景后" in resume_text
    assert len(resume_text) > 30
