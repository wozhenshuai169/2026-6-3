from __future__ import annotations

from .data_adapter import ScenicDataAdapter
from .memory import MemoryExtractor
from .schemas import AlgorithmRequest, PrivateAssistantResult
from .text_utils import contains_any


class PrivateAssistant:
    def __init__(self, data: ScenicDataAdapter, memory: MemoryExtractor) -> None:
        self.data = data
        self.memory = memory

    def handle(self, request: AlgorithmRequest) -> PrivateAssistantResult:
        text = request.text
        tags = self.memory.extract(text)

        if contains_any(text, ["走失", "走丢", "迷路", "找不到队伍", "队伍找不着", "晕", "头晕", "胸闷", "摔倒", "受伤", "中暑"]):
            return PrivateAssistantResult(
                answer="请先停在安全、显眼的位置，不要独自继续走动。我会把高风险情况通知团长，请同时联系附近工作人员。",
                needAskAuthorization=False,
                leaderMessage="游客反馈可能走失或身体不适，请团长立即确认位置并接管处理。",
                memoryTags=tags,
            )

        if contains_any(text, ["离队", "先走", "提前走", "自己走"]):
            return PrivateAssistantResult(
                answer="离队需要团长确认，我不能单独批准。你可以先说明原因，我会在你授权后通知团长。",
                needAskAuthorization=True,
                authorizationText="是否允许我把你的离队需求转告团长，请团长确认？",
                leaderMessage="游客提出离队或提前离开需求，请团长确认安全与集合安排。",
                memoryTags=tags,
            )

        facility = self.data.get_facility_hint(text, request.state.currentSpotId)
        if facility:
            return PrivateAssistantResult(
                answer=facility["content"],
                needAskAuthorization=contains_any(text, ["老人", "小孩", "走不动", "不舒服", "集合"]),
                authorizationText="这个情况可能影响集合时间，是否需要我通知团长？",
                leaderMessage="游客提出休息或设施协助需求，建议团长关注集合时间和行动便利性。",
                memoryTags=tags,
            )

        if contains_any(text, ["没听懂", "重复", "再讲", "慢一点", "慢点"]):
            return PrivateAssistantResult(
                answer="可以，我会用更慢、更直接的方式补充说明，并尽量不影响公共讲解节奏。",
                memoryTags={**tags, "explanationPreference": ["slower", "simpler"]},
            )

        return PrivateAssistantResult(
            answer="我会在私人频道处理这个需求，不会默认广播给全团。若需要团长协助，我会先征求你的授权。",
            needAskAuthorization=False,
            memoryTags=tags,
        )
