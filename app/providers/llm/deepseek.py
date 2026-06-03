"""DeepSeek LLM Provider —— 通过 OpenAI 兼容 API 调用 DeepSeek。"""

import logging
from typing import AsyncIterator

import httpx

from app.core.config import settings
from app.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class DeepSeekProvider(LLMProvider):
    """DeepSeek 真实 LLM Provider（OpenAI 兼容协议）。"""

    def __init__(self) -> None:
        self._api_key = settings.deepseek_api_key
        self._base_url = settings.deepseek_base_url.rstrip("/")
        self._model = settings.deepseek_model
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
        logger.info("[LLM] Using DeepSeek (model=%s, base_url=%s)", self._model, self._base_url)

    async def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        """非流式对话。"""
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
        }
        try:
            resp = await self._client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return LLMResponse(content=content)
        except httpx.HTTPError as e:
            logger.error("[DeepSeek] HTTP error: %s", e)
            raise LLMError(f"DeepSeek API 调用失败: {e}") from e

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        """流式对话，逐 chunk yield 文本。"""
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048),
            "stream": True,
        }
        try:
            async with self._client.stream("POST", "/chat/completions", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        chunk = line[6:]
                        if chunk == "[DONE]":
                            break
                        import json
                        try:
                            delta = json.loads(chunk)
                            content = delta["choices"][0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
        except httpx.HTTPError as e:
            logger.error("[DeepSeek] Stream error: %s", e)
            raise LLMError(f"DeepSeek 流式调用失败: {e}") from e


class LLMError(Exception):
    """LLM Provider 通用异常。"""
    pass
