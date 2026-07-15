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

    def resume_after_answer(self, state: TourState, question: str, answer: str = "") -> dict[str, str | bool]:
        next_segment = self.data.get_next_segment(state.currentSegmentId)
        resume_id = next_segment["segmentId"] if next_segment else state.currentSegmentId
        bridge = self._bridge(question, answer)
        next_text = next_segment["text"] if next_segment else "我们继续当前导览。"
        resume_text = f"{bridge}{next_text}"
        return {
            "shouldResume": state.isExplaining,
            "resumeSegmentId": resume_id,
            "resumeText": resume_text,
        }

    def _bridge(self, question: str, answer: str) -> str:
        summary = self._answer_summary(answer)
        if any(word in question for word in ["历史", "建于", "年代", "建的", "什么时候建", "落成", "开光"]):
            return f"{summary}了解了这个年代背景后，我们再看它和眼前建筑细节之间的关系。"
        if any(word in question for word in ["结构", "榫卯", "重檐"]):
            return f"{summary}结构问题很适合边看边理解，接下来请留意建筑的层次和受力方式。"
        if any(word in question for word in ["屋顶", "装饰", "工艺", "脊兽"]):
            return f"{summary}这个细节看得很准，接下来正好把视线放到工艺和装饰上。"
        if any(word in question for word in ["路线", "下一站", "怎么走"]):
            return f"{summary}路线清楚之后，我们先把当前这一站看完整，再按团长节奏前往下一处。"
        if any(word in question for word in ["厕所", "休息", "饮水", "出口", "服务"]):
            return f"{summary}服务设施可以私下继续确认，公共讲解这边我们先回到眼前内容。"
        if any(word in question for word in ["图片", "照片", "拍到", "这张图"]):
            return f"{summary}把图片里的对象和现场位置对应起来后，我们继续看它在整条动线里的作用。"
        if any(word in question for word in ["没听懂", "重复", "慢一点", "再讲"]):
            return f"{summary}我会把节奏放慢一点，接下来用更直接的方式继续说明。"
        return f"{summary}这个问题和我们正在看的内容正好能连起来。"

    def _answer_summary(self, answer: str) -> str:
        if not answer:
            return ""
        sentence = answer.split("。", 1)[0].strip()
        if not sentence:
            return ""
        if len(sentence) > 38:
            sentence = sentence[:38].rstrip("，、")
        return f"{sentence}。"
