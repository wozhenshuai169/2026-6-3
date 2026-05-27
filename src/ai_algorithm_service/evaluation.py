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
        for case in self.data.eval_cases:
            total += 1
            request = AlgorithmRequest(**case["request"])
            started = perf_counter()
            response = self.orchestrator.handle(request)
            latencies.append(perf_counter() - started)
            expected = case["expected"]
            if response.decision.decision == expected.get("decision"):
                decision_hits += 1
            if expected.get("privateSafe") and response.decision.channel != "public":
                no_private_broadcast += 1
            elif not expected.get("privateSafe"):
                no_private_broadcast += 1
            if expected.get("risk"):
                risk_total += 1
                if response.decision.needLeaderNotify and response.decision.riskLevel in ["medium", "high"]:
                    risk_recall += 1
            if expected.get("needsCitation"):
                rag_total += 1
                if response.citations:
                    citation_hits += 1
        return {
            "caseCount": total,
            "decisionAccuracy": round(decision_hits / total, 3),
            "privateLeakCount": total - no_private_broadcast,
            "riskEscalationRecall": round(risk_recall / risk_total, 3) if risk_total else 1.0,
            "citationHitRate": round(citation_hits / rag_total, 3) if rag_total else 1.0,
            "under10sRate": round(sum(1 for latency in latencies if latency <= 10) / total, 3),
            "avgLatencyMs": round(sum(latencies) / total * 1000, 2),
        }

