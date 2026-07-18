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
        explicit_spot_ids = self._explicit_spot_ids(question)
        candidates = self._candidate_chunks(question, state)
        for chunk in candidates:
            content_tokens = tokenize(" ".join([chunk["title"], chunk["content"], chunk.get("spotId", ""), chunk.get("topic", ""), chunk.get("audience", "")]))
            overlap = len(query_tokens & content_tokens)
            keyword_norm = min(1.0, overlap / 4)
            spot_norm = 1.0 if chunk.get("spotId") in explicit_spot_ids else 0.0
            current_spot_norm = (
                1.0
                if not explicit_spot_ids and chunk.get("spotId") == state.currentSpotId
                else 0.0
            )
            route_norm = 1.0 if state.currentRouteId in chunk.get("routeIds", []) else 0.0
            freshness_norm = self._freshness_norm(chunk.get("updatedAt"))
            source_norm = self._source_norm(chunk.get("sourceTier"))
            event_norm = 1.0 if chunk.get("type") == "operation_event" else 0.0
            intent_norm = self._intent_norm(question, chunk, explicit_spot_ids)
            if keyword_norm == 0 and event_norm == 0 and intent_norm == 0:
                continue
            score = (
                0.35 * keyword_norm
                + 0.35 * spot_norm
                + 0.08 * current_spot_norm
                + 0.05 * route_norm
                + 0.02 * freshness_norm
                + 0.45 * intent_norm
                + 0.10 * event_norm
            ) * source_norm
            if score > 0:
                scored.append(
                    (
                        score,
                        chunk,
                        {
                            "final": round(score, 3),
                            "keyword": round(keyword_norm, 3),
                            "spot": spot_norm,
                            "currentSpot": current_spot_norm,
                            "route": route_norm,
                            "freshness": round(freshness_norm, 3),
                            "intent": intent_norm,
                            "event": event_norm,
                            "source": source_norm,
                        },
                    )
                )
        scored.sort(key=lambda item: item[0], reverse=True)
        retrieval_scores = {chunk["chunkId"]: parts for _, chunk, parts in scored[:limit]}
        retrieved_ids = [chunk["chunkId"] for _, chunk, _ in scored[:limit]]
        if (
            not scored
            or scored[0][0] < 0.32
            or (not explicit_spot_ids and self._ambiguous_top_spots(scored))
        ):
            return QAResult(
                answer="当前资料中没有查到可靠信息。涉及路线、安全或实时安排时，建议以团长通知或景区公告为准。",
                citations=[],
                confidence=0.18,
                stateUpdate={"shouldResume": state.isExplaining, "resumeSegmentId": state.currentSegmentId},
                retrievedChunkIds=retrieved_ids,
                retrievalScores=retrieval_scores,
            )

        top = [chunk for score, chunk, _ in scored[:limit] if score >= 0.32]
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
        if top[0].get("sourceTier") == "unverified_reference":
            confidence = min(confidence, 0.55)
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
                    "sourceTier": "operator_event",
                    "routeIds": event.get("affectedRouteIds", []),
                    "content": event["content"],
                }
            )
        return chunks

    def _explicit_spot_ids(self, question: str) -> set[str]:
        matched: set[str] = set()
        if "灵山胜境" in question or "小灵山" in question:
            matched.add("lingshan_shengjing")
        for spot in self.data.vision_spots:
            aliases = [spot.get("spotName", ""), *spot.get("keywords", [])]
            if any(alias and len(alias) >= 2 and alias in question for alias in aliases):
                matched.add(spot["spotId"])
        return matched

    def _intent_norm(
        self,
        question: str,
        chunk: dict[str, Any],
        explicit_spot_ids: set[str],
    ) -> float:
        topic = str(chunk.get("topic") or "")
        chunk_type = str(chunk.get("type") or "")
        text = "".join([str(chunk.get("title") or ""), str(chunk.get("content") or "")])
        if any(word in question for word in ["路线", "怎么游", "怎么走", "哪条"]):
            if chunk_type != "route" and topic != "route":
                return 0.0
            route_ids = set(chunk.get("routeIds") or [])
            requested_route = None
            if any(word in question for word in ["亲子", "家庭"]):
                requested_route = "lingshan_family"
            elif any(word in question for word in ["自然", "风光"]):
                requested_route = "lingshan_nature"
            elif any(word in question for word in ["历史", "人文", "文化"]):
                requested_route = "lingshan_history"
            elif any(word in question for word in ["少走", "轻松", "体力"]):
                requested_route = "lingshan_easy"
            return 1.0 if not requested_route or requested_route in route_ids else 0.15
        if any(word in question for word in ["门票", "票价", "优惠", "多少钱"]):
            return 1.0 if topic == "ticket" else 0.0
        if any(word in question for word in ["现代", "开始建设", "工程奠基"]):
            return 1.0 if "1994年" in text else 0.0
        if "落成开光" in question:
            return 1.0 if "1997年11月15日" in text else 0.0
        if any(word in question for word in ["表演", "演出"]) and any(
            word in question for word in ["几点", "时间", "今天", "什么时候"]
        ):
            return 1.0 if topic == "operation" else 0.0
        if any(word in question for word in ["拍照", "拍摄", "摄影"]):
            return 1.0 if "拍摄" in text or topic == "safety" else 0.0
        if any(word in question for word in ["艺术", "看点", "工艺"]):
            return 1.0 if topic == "art" or ("木雕" in text and "壁画" in text) else 0.0
        if any(word in question for word in ["台阶", "多少级"]):
            return 1.0 if "216级" in text else 0.0
        if any(word in question for word in ["多高", "高度"]):
            return 1.0 if "88米" in text and "101.5米" in text else 0.0
        if any(word in question for word in ["多重", "重量"]):
            return 1.0 if "725吨" in text else 0.0
        if any(word in question for word in ["面积", "多大", "占地"]):
            if explicit_spot_ids and chunk.get("spotId") not in explicit_spot_ids:
                return 0.0
            return 1.0 if any(value in text for value in ["30万平方米", "7.2万平方米", "5000平方米"]) else 0.0
        return 0.0

    def _expand_query(self, question: str, state: TourState | None = None) -> str:
        additions = []
        if any(word in question for word in ["下一站", "怎么走", "路线", "往哪", "哪边", "接下来"]):
            additions.append("灵山胜境 游览路线 景点顺序 现场指引")
        if any(word in question for word in ["厕所", "厕锁", "洗手间", "卫生间", "饮水", "休息", "歇会", "出口"]):
            additions.append("卫生间 饮水点 休息区 附近设施 现场路牌")
        if any(word in question for word in ["轮椅", "急救", "服务中心", "借"]):
            additions.append("行动不便 观光车 无障碍通道 现场工作人员")
        if any(word in question for word in ["儿童", "孩子", "亲子", "活动"]):
            additions.append("亲子家庭 九龙灌浴 百子戏弥勒 梵宫 五印坛城")
        if any(word in question for word in ["开放", "几点", "时间"]):
            additions.append("当日公告 官方渠道 演出时间 开放状态")
        if any(word in question for word in ["啥时候", "什么时候", "修的", "建的", "历史"]):
            additions.append("灵山历史 唐代玄奘 1994年 1997年 建设历程")
        if any(word in question for word in ["多高", "高度", "多重", "重量", "台阶", "多少级"]):
            additions.append("灵山大佛 79米 莲花座9米 88米 101.5米 725吨 216级")
        if any(word in question for word in ["屋顶", "穹顶", "装饰", "建筑特色", "面积"]):
            additions.append("灵山梵宫 建筑面积 木雕 壁画 穹顶 五印坛城")
        if any(word in question for word in ["用途", "干啥", "做什么", "用的"]):
            additions.append("佛教文化 艺术展示 历史传播 参观体验")
        if any(word in question for word in ["怎么看", "观赏", "看法", "看石刻"]):
            additions.append("造型 图案 建筑层次 文化寓意 现场礼仪")
        if any(word in question for word in ["那", "刚才", "这个"]) and state and state.lastQuestion:
            additions.append(state.lastQuestion)
        return " ".join([question, *additions])

    def _compose_answer(self, question: str, chunks: list[dict]) -> str:
        primary = chunks[0]
        content = primary["content"].rstrip("。")
        if primary.get("sourceTier") == "unverified_reference":
            prefix = "未标注来源的资料包中提到，以下内容仍需以现场标识或景区工作人员说明核验："
        elif "开放" in question or "时间" in question:
            prefix = "按当前景区资料，"
        elif "路线" in question or "怎么走" in question:
            prefix = "结合当前路线，"
        else:
            prefix = "资料里提到，"
        return f"{prefix}{content}。"

    def _source_norm(self, source_tier: str | None) -> float:
        return {
            "official_verified": 1.0,
            "safety_policy": 1.0,
            "operator_event": 1.0,
            "unverified_reference": 0.72,
        }.get(source_tier or "", 0.8)

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
