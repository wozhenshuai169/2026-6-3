from __future__ import annotations

from .data_adapter import ScenicDataAdapter
from .decision import DecisionRouter
from .explanation import TourExplanation
from .memory import MemoryExtractor
from .private_assistant import PrivateAssistant
from .rag import ScenicRAG
from .routes import RouteRecommender
from .schemas import AlgorithmRequest, AlgorithmResponse, DecisionResult
from .vision import VisionRecognizer
from .voice import VoiceAdapter


class TourAIOrchestrator:
    def __init__(self, data: ScenicDataAdapter | None = None) -> None:
        self.data = data or ScenicDataAdapter()
        self.decision_router = DecisionRouter()
        self.rag = ScenicRAG(self.data)
        self.explanation = TourExplanation(self.data)
        self.memory = MemoryExtractor()
        self.private_assistant = PrivateAssistant(self.data, self.memory)
        self.vision = VisionRecognizer(self.data, self.rag)
        self.routes = RouteRecommender(self.data)
        self.voice = VoiceAdapter()

    def decide(self, request: AlgorithmRequest) -> DecisionResult:
        return self.decision_router.decide(request)

    def handle(self, request: AlgorithmRequest) -> AlgorithmResponse:
        decision = self.decide(request)
        events = [{"type": "decision", "payload": decision.model_dump()}]
        if request.channel == "public" and decision.channel == "private":
            events.append(
                {
                    "type": "suggest_private_channel",
                    "payload": {"reason": "该问题属于私人需求，不适合公共播报"},
                }
            )

        if decision.nextAction == "no_action":
            return AlgorithmResponse(decision=decision, events=events)

        if decision.nextAction == "ask_clarification":
            return AlgorithmResponse(
                decision=decision,
                answer="我没有听清，可以再说一遍或改用文字输入吗？",
                confidence=request.asrConfidence or 0.0,
                events=events,
            )

        if decision.nextAction == "human_takeover":
            private = self.private_assistant.handle(request)
            return AlgorithmResponse(
                decision=decision,
                answer=private.answer,
                private=private,
                memoryTags=private.memoryTags,
                events=events + [{"type": "leader_notify", "payload": {"message": private.leaderMessage}}],
            )

        if decision.nextAction == "ask_authorization_then_notify_leader":
            private = self.private_assistant.handle(request)
            if request.authorizationGranted:
                private.needAskAuthorization = False
            return AlgorithmResponse(
                decision=decision,
                answer=private.answer,
                private=private,
                memoryTags=private.memoryTags,
                events=events,
            )

        if decision.nextAction == "private_assistant":
            private = self.private_assistant.handle(request)
            return AlgorithmResponse(
                decision=decision,
                answer=private.answer,
                private=private,
                memoryTags=private.memoryTags,
                events=events,
            )

        if decision.nextAction == "vision_recognize":
            vision = self.vision.recognize(request)
            state_update = {"shouldResume": request.state.isExplaining, "resumeSegmentId": request.state.currentSegmentId}
            if decision.needInterrupt:
                state_update = {
                    **state_update,
                    **self.explanation.resume_after_answer(request.state, request.text or "图片识别", vision.answer),
                }
            return AlgorithmResponse(
                decision=decision,
                answer=vision.answer,
                citations=vision.citations,
                confidence=vision.confidence,
                vision=vision,
                stateUpdate=state_update,
                events=events,
            )

        if decision.nextAction == "summarize_discussion":
            answer = "当前讨论主要围绕景点信息、路线安排和游客需求。涉及安全或离队事项仍需团长确认。"
            return AlgorithmResponse(decision=decision, answer=answer, confidence=0.7, events=events)

        qa = self.rag.query(request.text, request.state)
        state_update = qa.stateUpdate
        if decision.needInterrupt:
            state_update = {**state_update, **self.explanation.resume_after_answer(request.state, request.text, qa.answer)}
        return AlgorithmResponse(
            decision=decision,
            answer=qa.answer,
            citations=qa.citations,
            confidence=qa.confidence,
            stateUpdate=state_update,
            events=events,
        )

    def recommend_routes(self, request: AlgorithmRequest) -> AlgorithmResponse:
        decision = DecisionResult(
            decision="private_reply" if request.channel == "private" else "public_reply",
            channel=request.channel,
            reason="执行个性化路线推荐",
            nextAction="route_recommend",
        )
        recommendations = self.routes.recommend(request.profile, request.state)
        return AlgorithmResponse(decision=decision, routes=recommendations, answer=recommendations[0].reason if recommendations else None)

    def extract_memory(self, request: AlgorithmRequest) -> dict:
        return self.memory.extract(request.text)

    def handle_voice(self, request: AlgorithmRequest) -> tuple:
        asr = self.voice.asr(
            audio_format=request.audioFormat,
            audio_path=request.audioPath,
            audio_url=request.audioUrl,
            text_hint=request.text,
        )
        voice_request = request.model_copy(
            update={
                "text": asr.text,
                "inputMode": "voice",
                "asrConfidence": asr.confidence,
                "audioFormat": asr.format,
            }
        )
        response = self.handle(voice_request)
        tts = self.voice.tts(response.answer or "")
        return asr, response, tts
