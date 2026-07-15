from __future__ import annotations

from time import perf_counter

from .data_adapter import ScenicDataAdapter
from .orchestrator import TourAIOrchestrator
from .schemas import AlgorithmRequest


class EvaluationHarness:
    def __init__(self, orchestrator: TourAIOrchestrator | None = None) -> None:
        self.orchestrator = orchestrator or TourAIOrchestrator()
        self.data: ScenicDataAdapter = self.orchestrator.data

    def run(self) -> dict:
        total = 0
        decision_hits = 0
        no_private_broadcast = 0
        risk_recall = 0
        risk_total = 0
        citation_hits = 0
        rag_total = 0
        latencies = []
        low_asr_hits = 0
        low_asr_total = 0
        resume_hits = 0
        resume_total = 0
        answer_mismatch_total = 0
        answer_mismatch_hits = 0
        unsupported_total = 0
        unsupported_hits = 0
        private_sensitive_total = 0
        private_leak_hits = 0
        low_confidence_total = 0
        low_confidence_hits = 0
        factual_total = 0
        factual_hits = 0
        for case in self.data.eval_cases:
            total += 1
            request = AlgorithmRequest(**case["request"])
            started = perf_counter()
            response = self.orchestrator.handle(request)
            latencies.append(perf_counter() - started)
            expected = case["expected"]
            if response.decision.decision == expected.get("decision"):
                decision_hits += 1
            is_private_sensitive = bool(expected.get("privateSafe"))
            if is_private_sensitive:
                private_sensitive_total += 1
            leaked_private = is_private_sensitive and response.decision.channel == "public"
            if leaked_private:
                private_leak_hits += 1
            if is_private_sensitive and not leaked_private:
                no_private_broadcast += 1
            elif not is_private_sensitive:
                no_private_broadcast += 1
            if expected.get("risk"):
                risk_total += 1
                if response.decision.needLeaderNotify and response.decision.riskLevel in ["medium", "high"]:
                    risk_recall += 1
            if expected.get("needsCitation"):
                rag_total += 1
                if response.citations:
                    citation_hits += 1
            if request.inputMode == "voice" and request.asrConfidence is not None and request.asrConfidence < 0.6:
                low_asr_total += 1
                low_confidence_total += 1
                if response.decision.nextAction == "ask_clarification":
                    low_asr_hits += 1
                    low_confidence_hits += 1
            if response.decision.needInterrupt and response.decision.nextAction in ["public_rag_answer", "vision_recognize"]:
                resume_total += 1
                if response.stateUpdate.get("resumeText") and response.stateUpdate.get("resumeSegmentId"):
                    resume_hits += 1
            answer = response.answer or ""
            if expected.get("answerContainsAny"):
                answer_mismatch_total += 1
                if not self._contains_any(answer, expected["answerContainsAny"]):
                    answer_mismatch_hits += 1
            if expected.get("expectNoReliableInfo"):
                answer_mismatch_total += 1
                if "没有查到可靠信息" not in answer:
                    answer_mismatch_hits += 1
                    unsupported_hits += 1
                unsupported_total += 1
            if expected.get("grounded") or expected.get("needsCitation"):
                unsupported_total += 1
                if answer and "没有查到可靠信息" not in answer and not response.citations:
                    unsupported_hits += 1
            if expected.get("category") in {"事实问答", "历史文化", "景点特色", "易变信息", "参观规则"}:
                factual_total += 1
                contains_expected = not expected.get("answerContainsAny") or self._contains_any(
                    answer, expected["answerContainsAny"]
                )
                grounded = not expected.get("needsCitation") or bool(response.citations)
                if contains_expected and grounded and response.decision.decision == expected.get("decision"):
                    factual_hits += 1
        vision_feature_hits = 0
        for spot in self.data.vision_spots:
            request = AlgorithmRequest(channel="public", text="介绍这张图", imageUrl=spot["images"][0])
            response = self.orchestrator.handle(request)
            if response.vision and response.vision.visualFeatures:
                vision_feature_hits += 1
        route_response = self.orchestrator.recommend_routes(
            AlgorithmRequest(profile={"memoryTags": {"stamina": "low", "companions": ["elderly"], "availableMinutes": 40}})
        )
        route_score_consistent = all(sum(route.scoreBreakdown.values()) == route.score for route in route_response.routes)
        return {
            "caseCount": total,
            "decisionAccuracy": round(decision_hits / total, 3),
            "privateLeakCount": total - no_private_broadcast,
            "riskEscalationRecall": round(risk_recall / risk_total, 3) if risk_total else 1.0,
            "citationHitRate": round(citation_hits / rag_total, 3) if rag_total else 1.0,
            "under10sRate": round(sum(1 for latency in latencies if latency <= 10) / total, 3),
            "localUnder5sRate": round(sum(1 for latency in latencies if latency <= 5) / total, 3),
            "avgLatencyMs": round(sum(latencies) / total * 1000, 2),
            "factualAccuracy": round(factual_hits / factual_total, 3) if factual_total else 1.0,
            "lowAsrClarificationRate": round(low_asr_hits / low_asr_total, 3) if low_asr_total else 1.0,
            "answerMismatchRate": round(answer_mismatch_hits / answer_mismatch_total, 3) if answer_mismatch_total else 0.0,
            "unsupportedAnswerRate": round(unsupported_hits / unsupported_total, 3) if unsupported_total else 0.0,
            "privateInfoLeakRate": round(private_leak_hits / private_sensitive_total, 3) if private_sensitive_total else 0.0,
            "lowConfidenceFallbackRate": round(low_confidence_hits / low_confidence_total, 3) if low_confidence_total else 1.0,
            "visionFeatureCoverage": round(vision_feature_hits / len(self.data.vision_spots), 3),
            "routeScoreBreakdownConsistent": route_score_consistent,
            "resumeTextCoverage": round(resume_hits / resume_total, 3) if resume_total else 1.0,
        }

    def _contains_any(self, text: str, candidates: list[str]) -> bool:
        return any(candidate in text for candidate in candidates)
