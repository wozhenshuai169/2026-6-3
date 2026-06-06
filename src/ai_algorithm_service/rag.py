from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .data_adapter import ScenicDataAdapter
from .schemas import Citation, QAResult, TourState
from .text_utils import tokenize


class ScenicRAG:
    def __init__(self, data: ScenicDataAdapter) -> None:
        self.data = data

    def query(self, question: str, state: TourState, limit: int = 3) -> QAResult:
        scored: list[tuple[float, dict[str, Any], dict[str, float]]] = []
        expanded_question = self._expand_query(question, state)
        query_tokens = tokenize(expanded_question)
        candidates = self._candidate_chunks(question, state)
        for chunk in candidates:
            content_tokens = tokenize(" ".join([chunk["title"], chunk["content"], chunk.get("spotId", ""), chunk.get("topic", ""), chunk.get("audience", "")]))
            overlap = len(query_tokens & content_tokens)
            keyword_norm = min(1.0, overlap / 4)
            spot_norm = 1.0 if chunk.get("spotId") == state.currentSpotId else 0.0
            route_norm = 1.0 if state.currentRouteId in chunk.get("routeIds", []) else 0.0
            freshness_norm = self._freshness_norm(chunk.get("updatedAt"))
            event_norm = 1.0 if chunk.get("type") == "operation_event" else 0.0
            if keyword_norm == 0 and event_norm == 0:
                continue
            score = (
                0.45 * keyword_norm
                + 0.20 * spot_norm
                + 0.15 * route_norm
                + 0.10 * freshness_norm
                + 0.10 * event_norm
            )
            if score > 0:
                scored.append(
                    (
                        score,
                        chunk,
                        {
                            "final": round(score, 3),
                            "keyword": round(keyword_norm, 3),
                            "spot": spot_norm,
                            "route": route_norm,
                            "freshness": round(freshness_norm, 3),
                            "event": event_norm,
                        },
                    )
                )
        scored.sort(key=lambda item: item[0], reverse=True)
        retrieval_scores = {chunk["chunkId"]: parts for _, chunk, parts in scored[:limit]}
        retrieved_ids = [chunk["chunkId"] for _, chunk, _ in scored[:limit]]
        if not scored or scored[0][0] < 0.4 or self._ambiguous_top_spots(scored):
            return QAResult(
                answer="当前资料中没有查到可靠信息。涉及路线、安全或实时安排时，建议以团长通知或景区公告为准。",
                citations=[],
                confidence=0.18,
                stateUpdate={"shouldResume": state.isExplaining, "resumeSegmentId": state.currentSegmentId},
                retrievedChunkIds=retrieved_ids,
                retrievalScores=retrieval_scores,
            )

        top = [chunk for score, chunk, _ in scored[:limit] if score >= 0.4]
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
        confidence = min(0.95, max(0.4, scored[0][0]))
        return QAResult(
            answer=answer,
            citations=citations,
            confidence=round(confidence, 2),
            stateUpdate={"shouldResume": state.isExplaining, "resumeSegmentId": state.currentSegmentId},
            retrievedChunkIds=retrieved_ids,
            retrievalScores=retrieval_scores,
        )

    def _candidate_chunks(self, question: str, state: TourState) -> list[dict[str, Any]]:
        chunks = [
            chunk
            for chunk in self.data.chunks
            if chunk.get("type") != "qa_policy" and chunk.get("topic") != "qa_policy"
        ]
        operation_events = self.data.query_operation_events(question, state.currentSpotId, state.currentRouteId)
        for event in operation_events:
            chunks.append(
                {
                    "chunkId": event["eventId"],
                    "spotId": (event.get("affectedSpotIds") or [state.currentSpotId])[0],
                    "title": event["title"],
                    "type": "operation_event",
                    "source": event.get("source", "景区运营事件"),
                    "updatedAt": event.get("updatedAt"),
                    "routeIds": event.get("affectedRouteIds", []),
                    "content": event["content"],
                }
            )
        return chunks

    def _expand_query(self, question: str, state: TourState | None = None) -> str:
        additions = []
        if any(word in question for word in ["下一站", "怎么走", "路线", "往哪", "哪边", "接下来"]):
            additions.append("参观动线 右侧廊道 前往 步行 路线")
        if any(word in question for word in ["厕所", "厕锁", "洗手间", "卫生间", "饮水", "休息", "歇会", "出口"]):
            additions.append("游客服务 设施 位置")
        if any(word in question for word in ["轮椅", "急救", "服务中心", "借"]):
            additions.append("游客服务中心 急救包 轮椅借用 咨询")
        if any(word in question for word in ["儿童", "孩子", "亲子", "活动"]):
            additions.append("儿童 亲子 任务卡 家庭")
        if any(word in question for word in ["开放", "几点", "时间"]):
            additions.append("开放时间 景区公告")
        if any(word in question for word in ["啥时候", "什么时候", "修的", "建的", "历史"]):
            additions.append("历史介绍 始建 明代 清代 修缮")
        if any(word in question for word in ["屋顶", "脊兽", "装饰", "建筑特色"]):
            additions.append("屋顶装饰 灰瓦 脊兽 建筑看点")
        if any(word in question for word in ["用途", "干啥", "做什么", "用的"]):
            additions.append("用途 报时 礼仪 展陈 功能")
        if any(word in question for word in ["怎么看", "观赏", "看法", "看石刻"]):
            additions.append("观赏方式 题额 正文 刻痕 书体")
        if any(word in question for word in ["那", "刚才", "这个"]) and state and state.lastQuestion:
            additions.append(state.lastQuestion)
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

    def _freshness_norm(self, updated_at: str | None) -> float:
        if not updated_at:
            return 0.5
        try:
            updated = datetime.fromisoformat(updated_at).replace(tzinfo=timezone.utc)
        except ValueError:
            return 0.5
        days = max(0, (datetime.now(timezone.utc) - updated).days)
        return max(0.0, 1.0 - days / 180)

    def _ambiguous_top_spots(self, scored: list[tuple[float, dict[str, Any], dict[str, float]]]) -> bool:
        if len(scored) < 2:
            return False
        first_score, first_chunk, _ = scored[0]
        second_score, second_chunk, _ = scored[1]
        if abs(first_score - second_score) >= 0.05:
            return False
        return first_chunk.get("spotId") != second_chunk.get("spotId")
