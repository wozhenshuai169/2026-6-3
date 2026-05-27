from __future__ import annotations

from .data_adapter import ScenicDataAdapter
from .rag import ScenicRAG
from .schemas import AlgorithmRequest, VisionResult
from .text_utils import contains_any


class VisionRecognizer:
    def __init__(self, data: ScenicDataAdapter, rag: ScenicRAG) -> None:
        self.data = data
        self.rag = rag

    def recognize(self, request: AlgorithmRequest) -> VisionResult:
        text = " ".join(part for part in [request.text, request.imageUrl or ""] if part)
        candidates = {
            "钟楼": ["钟楼", "bell", "zhonglou"],
            "鼓楼": ["鼓楼", "drum", "gulou"],
            "主展厅": ["主展厅", "展厅", "main_hall"],
            "石刻": ["石刻", "碑", "stone"],
            "庭院": ["庭院", "院落", "courtyard"],
        }
        recognized = None
        for name, keywords in candidates.items():
            if contains_any(text, keywords):
                recognized = name
                break
        if not recognized:
            current = request.state.currentSpotId
            related = [chunk["title"] for chunk in self.data.get_spot_chunks(current)[:2]]
            return VisionResult(
                recognizedObject=None,
                confidence=0.28,
                answer="我还不能可靠确认图片里的对象。可以结合当前位置先看这些候选信息，也请补充拍摄角度或文字描述。",
                relatedSpots=related,
                recommendedAction="ask_for_more_context",
            )

        qa = self.rag.query(f"介绍{recognized}", request.state)
        return VisionResult(
            recognizedObject=recognized,
            confidence=0.82,
            answer=f"你拍到的可能是{recognized}。{qa.answer}",
            citations=qa.citations,
            relatedSpots=self._related_spots(recognized),
            recommendedAction="rag_explain",
        )

    def _related_spots(self, recognized: str) -> list[str]:
        mapping = {
            "钟楼": ["鼓楼", "主展厅"],
            "鼓楼": ["钟楼", "主展厅"],
            "主展厅": ["钟楼", "庭院"],
            "石刻": ["主展厅", "庭院"],
            "庭院": ["主展厅", "出口"],
        }
        return mapping.get(recognized, [])

