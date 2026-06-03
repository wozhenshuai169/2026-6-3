"""Mock LLM Provider —— 当 DEEPSEEK_API_KEY 未设置时降级使用。

保持与原有 app/services/ai.py 相同的 Mock 行为。
"""

import logging
from typing import AsyncIterator

from app.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class MockLLMProvider(LLMProvider):
    """Mock LLM：返回模板化回答，不调用任何外部 API。"""

    def __init__(self) -> None:
        logger.info("[LLM] Using Mock (no API key configured)")

    def _extract_question(self, messages: list[dict]) -> str:
        """从 messages 中提取最后一条用户消息作为问题。"""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return str(msg.get("content", ""))
        return ""

    def _build_answer(self, question: str, context: dict | None = None) -> str:
        """构建 Mock 回答。"""
        spot = context.get("current_spot", "") if context else ""
        if spot:
            return (
                f"关于「{question}」的解答：当前位于 {spot}，"
                f"这里是模拟答案，后续将接入真实 AI。"
            )
        return f"关于「{question}」的解答：这里是模拟答案（Mock 模式），请配置 DEEPSEEK_API_KEY 以启用真实 AI。"

    async def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        question = self._extract_question(messages)
        context = kwargs.pop("context", None)
        answer = self._build_answer(question, context)
        return LLMResponse(content=answer)

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        question = self._extract_question(messages)
        context = kwargs.pop("context", None)
        answer = self._build_answer(question, context)
        # Mock 流式：每次返回一个字符（模拟逐字输出）
        chunk_size = 3
        for i in range(0, len(answer), chunk_size):
            yield answer[i:i + chunk_size]
