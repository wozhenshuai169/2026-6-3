from __future__ import annotations

from .data_adapter import ScenicDataAdapter
from .schemas import Citation, QAResult, TourState
from .text_utils import tokenize


class ScenicRAG:
    def __init__(self, data: ScenicDataAdapter) -> None:
        self.data = data

    def query(self, question: str, state: TourState, limit: int = 3) -> QAResult:
        scored: list[tuple[float, dict]] = []
        expanded_question = self._expand_query(question)
        query_tokens = tokenize(expanded_question)
        for chunk in self.data.chunks:
            content_tokens = tokenize(" ".join([chunk["title"], chunk["content"], chunk.get("spotId", "")]))
            overlap = len(query_tokens & content_tokens)
            if overlap == 0:
                continue
            spot_bonus = 2 if chunk.get("spotId") == state.currentSpotId else 0
            route_bonus = 1 if state.currentRouteId in chunk.get("routeIds", []) else 0
            score = overlap + spot_bonus + route_bonus
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        if not scored or scored[0][0] < 2:
            return QAResult(
                answer="当前资料中没有查到可靠信息。涉及路线、安全或实时安排时，建议以团长通知或景区公告为准。",
                citations=[],
                confidence=0.18,
                stateUpdate={"shouldResume": state.isExplaining, "resumeSegmentId": state.currentSegmentId},
            )

        top = [chunk for _, chunk in scored[:limit]]
        citations = [
            Citation(
                chunkId=chunk["chunkId"],
                title=chunk["title"],
                source=chunk.get("source", "景区资料"),
                updatedAt=chunk.get("updatedAt"),
            )
            for chunk in top
        ]
        answer = self._compose_answer(question, top)
        confidence = min(0.95, 0.55 + scored[0][0] / 20)
        return QAResult(
            answer=answer,
            citations=citations,
            confidence=round(confidence, 2),
            stateUpdate={"shouldResume": state.isExplaining, "resumeSegmentId": state.currentSegmentId},
        )

    def _expand_query(self, question: str) -> str:
        additions = []
        if any(word in question for word in ["下一站", "怎么走", "路线", "往哪"]):
            additions.append("参观动线 右侧廊道 前往 步行 路线")
        if any(word in question for word in ["厕所", "洗手间", "饮水", "休息", "出口"]):
            additions.append("游客服务 设施 位置")
        if any(word in question for word in ["开放", "几点", "时间"]):
            additions.append("开放时间 景区公告")
        return " ".join([question, *additions])

    def _compose_answer(self, question: str, chunks: list[dict]) -> str:
        primary = chunks[0]
        content = primary["content"].rstrip("。")
        if "开放" in question or "时间" in question:
            prefix = "按当前景区资料，"
        elif "路线" in question or "怎么走" in question:
            prefix = "结合当前路线，"
        else:
            prefix = "资料里提到，"
        return f"{prefix}{content}。"
