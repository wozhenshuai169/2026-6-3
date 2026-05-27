from __future__ import annotations

from .data_adapter import ScenicDataAdapter
from .schemas import QAResult, TourState


class TourExplanation:
    def __init__(self, data: ScenicDataAdapter) -> None:
        self.data = data

    def next_segment(self, state: TourState) -> QAResult:
        segment = self.data.get_next_segment(state.currentSegmentId)
        if not segment:
            return QAResult(answer="当前讲解段落已经结束，我们可以等待团长安排下一站。", confidence=0.7)
        return QAResult(
            answer=segment["text"],
            confidence=0.9,
            stateUpdate={"currentSegmentId": segment["segmentId"], "phase": "explaining"},
        )

    def resume_after_answer(self, state: TourState, question: str) -> dict[str, str | bool]:
        next_segment = self.data.get_next_segment(state.currentSegmentId)
        resume_id = next_segment["segmentId"] if next_segment else state.currentSegmentId
        bridge = "这个问题和我们正在看的内容正好能连起来。"
        if any(word in question for word in ["历史", "建于", "年代"]):
            bridge = "刚才这个问题也和这里的历史沿革有关。"
        elif any(word in question for word in ["屋顶", "装饰", "工艺"]):
            bridge = "这个细节看得很准，接下来正好可以看建筑工艺。"
        elif any(word in question for word in ["路线", "下一站"]):
            bridge = "了解路线后，我们再把注意力放回眼前这一站。"
        return {
            "shouldResume": state.isExplaining,
            "resumeSegmentId": resume_id,
            "resumeText": f"{bridge}{next_segment['text'] if next_segment else '我们继续当前导览。'}",
        }

