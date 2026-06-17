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
    provider_name = "qwen_vl"
    """Qwen-VL 多模态识景 Provider —— 百炼 DashScope 真实调用。"""

    def __init__(self) -> None:
        self._api_key = settings.qwen_vl_api_key
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
        """调用 Qwen-VL 识别图片内容，景区优先，同时支持人物/物体/场景识别。"""
        system_prompt = (
            "你是一个智能图片识别助手，服务于旅游景区导览场景。\n\n"
            "## 识别优先级（从高到低）：\n"
            "1. **景区/建筑/地标**：优先识别图片中的景点、建筑、自然风光、历史遗迹等\n"
            "2. **人物**：如果图片的主体是人物（单人/多人/雕像/画像），如实描述人物特征\n"
            "3. **物体/动物**：如果主体是特定物体、动物、艺术品等，如实描述\n"
            "4. **场景/氛围**：如果以上都不适用，描述整体场景\n\n"
            "## 分类标签（category）：\n"
            '- "spot" — 景点/建筑/地标/自然风光\n'
            '- "person" — 人物照片（真人/雕像/画像）\n'
            '- "object" — 物体/动物/艺术品\n'
            '- "scene" — 室内场景/氛围图/插画\n'
            '- "unknown" — 无法判断\n\n'
            "## 输出格式（严格 JSON）：\n"
            '{"category": "分类标签", "spotName": "名称", "confidence": 0.85, '
            '"description": "详细中文描述", '
            '"visualFeatures": ["特征1", "特征2"], "relatedSpots": ["相关景点1"]}\n\n'
            "## 重要规则：\n"
            "- 是人物就标 person，不要硬说成景点\n"
            "- 景点不存在时 spotName 用描述性短语（如「黄色上衣的女性」），confidence 如实降低\n"
            "- 描述要具体：服饰颜色款式、发型、姿态、背景环境等"
        )

        user_prompt = "请识别这张图片的内容。"
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

        except httpx.HTTPStatusError as e:
            resp_body = e.response.text if e.response else ""
            # 内容审核拦截：返回明确提示而非静默降级
            if "data_inspection_failed" in resp_body or "inappropriate" in resp_body:
                logger.warning("[Qwen-VL] Content moderation blocked this image")
                return VisionResult(
                    spot_id="rejected",
                    spot_name="图片未通过内容审核",
                    confidence=0.0,
                    description="该图片被云端内容安全策略拦截，无法识别。请更换图片或联系管理员。",
                    related_spots=[],
                    visual_features=[],
                    category="unknown",
                )
            logger.error("[Qwen-VL] API error: %s — %s", e, resp_body[:300])
            # 其他HTTP错误降级到 Mock
            return VisionResult(
                spot_id="error",
                spot_name="Vision provider error",
                confidence=0.0,
                description=f"Qwen-VL request failed: {e}",
                related_spots=[],
                visual_features=[],
                category="unknown",
            )

        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
            logger.error("[Qwen-VL] API error: %s", e)
            # 降级到 Mock
            return VisionResult(
                spot_id="error",
                spot_name="Vision provider error",
                confidence=0.0,
                description=f"Qwen-VL request failed: {e}",
                related_spots=[],
                visual_features=[],
                category="unknown",
            )

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
                "category": "unknown",
                "spotName": hint or "未知",
                "confidence": 0.5,
                "description": content.strip()[:500],
                "visualFeatures": [],
                "relatedSpots": [],
            }

        category = parsed.get("category", "spot")
        spot_name = parsed.get("spotName", hint or "未知")
        confidence = float(parsed.get("confidence", 0.5))

        # 人物/物体/场景类：spot_id 用描述性短语代替
        if category in ("person", "object", "scene", "unknown"):
            spot_id = parsed.get("spotId", category)
        else:
            spot_id = parsed.get("spotId", hint or "")

        return VisionResult(
            spot_id=spot_id,
            spot_name=spot_name,
            confidence=confidence,
            description=str(parsed.get("description", "")),
            related_spots=[
                {"spotId": s, "spotName": s}
                for s in parsed.get("relatedSpots", [])
            ],
            visual_features=list(parsed.get("visualFeatures", [])),
            category=category,
        )
