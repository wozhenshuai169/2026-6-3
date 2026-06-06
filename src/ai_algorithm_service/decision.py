from __future__ import annotations

from .schemas import AlgorithmRequest, DecisionResult
from .text_utils import contains_any


class DecisionRouter:
    """Rules-first intervention router with deterministic safety boundaries."""

    emergency_keywords = ["走失", "走丢", "迷路", "找不到队伍", "队伍找不着", "集合走散", "走散", "晕", "头晕", "胸闷", "摔倒", "受伤", "中暑", "事故", "火灾"]
    safety_keywords = ["身体不舒服", "不舒服", "低血糖", "孩子不见", "小孩不见", "娃不见", "老人不见", "封路", "路线封闭", "暴雨", "雷电", "突发天气", "台风", "塌方"]
    leave_keywords = ["离队", "先走", "不跟团", "自己走", "提前走"]
    private_keywords = ["厕所", "厕锁", "洗手间", "卫生间", "茅房", "休息", "歇会", "累了", "出口", "饮水", "口渴", "走不动", "老人", "小孩", "孩子", "没听懂", "重复", "少走路"]
    public_question_keywords = [
        "为什么",
        "什么",
        "啥",
        "哪里",
        "哪边",
        "多久",
        "怎么",
        "应该",
        "能",
        "吗",
        "历史",
        "建于",
        "开放",
        "路线",
        "屋顶",
        "脊兽",
        "装饰",
        "建筑",
        "这个",
        "介绍",
        "讲讲",
        "讲下",
    ]
    idle_keywords = ["哈哈", "好的", "知道了", "谢谢", "没事", "嗯", "哦"]
    summary_keywords = ["总结", "概括", "刚才讨论"]

    def decide(self, request: AlgorithmRequest) -> DecisionResult:
        text = request.text.strip()
        if request.inputMode == "voice" and request.asrConfidence is not None and request.asrConfidence < 0.6:
            return DecisionResult(
                decision="ask_clarification",
                channel="private" if request.channel == "private" else "public",
                reason="语音识别置信度过低，需要用户确认后再介入",
                nextAction="ask_clarification",
            )

        if request.imageUrl:
            return DecisionResult(
                decision="public_reply" if request.channel == "public" else "private_reply",
                channel=request.channel,
                needInterrupt=request.state.isExplaining and request.channel == "public",
                reason="游客提交图片，需要进行图文识景并接入知识库回答",
                nextAction="vision_recognize",
            )

        if contains_any(text, self.emergency_keywords + self.safety_keywords):
            return DecisionResult(
                decision="emergency_alert",
                channel="leader",
                needInterrupt=True,
                needLeaderNotify=True,
                riskLevel="high",
                reason="命中走失、身体不适或安全事故等高风险表达",
                nextAction="human_takeover",
            )

        if contains_any(text, self.leave_keywords):
            return DecisionResult(
                decision="notify_leader",
                channel="leader",
                needInterrupt=False,
                needLeaderNotify=True,
                riskLevel="medium",
                reason="离队或提前离开需要团长确认，AI 不单独批准",
                nextAction="ask_authorization_then_notify_leader",
            )

        if contains_any(text, self.summary_keywords):
            return DecisionResult(
                decision="summarize_discussion",
                channel=request.channel,
                reason="用户请求总结当前讨论",
                nextAction="summarize_discussion",
            )

        if request.channel == "private" or contains_any(text, self.private_keywords):
            return DecisionResult(
                decision="private_reply",
                channel="private",
                reason="游客提出私人需求或来自私人频道，默认不广播",
                nextAction="private_assistant",
            )

        if contains_any(text, self.public_question_keywords):
            return DecisionResult(
                decision="interrupt_and_answer" if request.state.isExplaining else "public_reply",
                channel="public",
                needInterrupt=request.state.isExplaining,
                riskLevel="low",
                reason="游客提出与导览相关的公共问题",
                nextAction="public_rag_answer",
            )

        if contains_any(text, self.idle_keywords) or len(text) <= 4:
            return DecisionResult(
                decision="ignore",
                channel=request.channel,
                reason="普通闲聊或确认反馈，不需要 AI 介入",
                nextAction="no_action",
            )

        return DecisionResult(
            decision="public_reply" if request.channel == "public" else "private_reply",
            channel=request.channel,
            riskLevel="low",
            reason="规则未完全覆盖，采用保守问答兜底",
            nextAction="public_rag_answer" if request.channel == "public" else "private_assistant",
        )
