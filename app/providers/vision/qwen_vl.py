"""Qwen-VL Vision Provider —— 通过阿里云百炼 DashScope 实现真实多模态识景。

API: OpenAI 兼容协议，base_url=https://dashscope.aliyuncs.com/compatible-mode/v1
Model: qwen-vl-plus / qwen-vl-max
"""

import json
import logging
from typing import AsyncIterator

import httpx

from app.core.config import settings
from app.providers.base import VisionProvider, VisionResult

logger = logging.getLogger(__name__)


class QwenVLVisionProvider(VisionProvider):
    """Qwen-VL 多模态识景 Provider —— 百炼 DashScope 真实调用。"""

    def __init__(self) -> None:
        self._api_key = settings.vision_api_key
        self._base_url = settings.vision_base_url.rstrip("/")
        self._model = settings.vision_model
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
        logger.info("[Vision] Using Qwen-VL (model=%s, base_url=%s)", self._model, self._base_url)

    async def recognize(self, image_url: str, hint: str = "") -> VisionResult:
        """调用 Qwen-VL 识别图片中的景点，返回结构化结果。"""
        system_prompt = (
            "你是一个景区图片识别助手。根据图片内容识别景点名称、"
            "视觉特征（建筑风格、颜色、材质等），并用中文描述。"
            "返回 JSON 格式："
            '{"spotName": "景点名", "confidence": 0.85, "description": "描述",'
            '"visualFeatures": ["特征1", "特征2"], "relatedSpots": ["相关景点1"]}'
        )

        user_prompt = "请识别这张图片中的景点。"
        if hint:
            user_prompt += f" 提示：可能在 {hint} 附近。"

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": user_prompt},
                ],
            },
        ]

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024,
        }

        try:
            resp = await self._client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            # 尝试解析 JSON 响应
            return self._parse_response(content, hint)

        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
            logger.error("[Qwen-VL] API error: %s", e)
            # 降级到 Mock
            from app.providers.vision.mock import MockVisionProvider
            logger.warning("[Qwen-VL] Falling back to Mock vision")
            mock = MockVisionProvider()
            return await mock.recognize(image_url, hint=hint)

    def _parse_response(self, content: str, hint: str = "") -> VisionResult:
        """解析 Qwen-VL 返回的 JSON 或文本。"""
        # 尝试提取 JSON 块
        try:
            # 可能是 ```json ... ``` 包裹的
            if "```json" in content:
                start = content.index("```json") + 7
                end = content.index("```", start)
                content = content[start:end]
            elif "```" in content:
                start = content.index("```") + 3
                end = content.index("```", start)
                content = content[start:end]
            parsed = json.loads(content.strip())
        except (json.JSONDecodeError, ValueError):
            # 非 JSON 格式，当作纯文本描述
            parsed = {
                "spotName": hint or "未知景点",
                "confidence": 0.75,
                "description": content.strip()[:500],
                "visualFeatures": [],
                "relatedSpots": [],
            }

        return VisionResult(
            spot_id=parsed.get("spotId", hint or ""),
            spot_name=parsed.get("spotName", hint or "未知景点"),
            confidence=float(parsed.get("confidence", 0.8)),
            description=str(parsed.get("description", "")),
            related_spots=[
                {"spotId": s, "spotName": s}
                for s in parsed.get("relatedSpots", [])
            ],
            visual_features=list(parsed.get("visualFeatures", [])),
        )
