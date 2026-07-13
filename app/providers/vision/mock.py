"""Mock Vision Provider —— 当视觉 API Key 未设置时降级使用。

对齐 src/ai_algorithm_service/vision.py 的 VisionProvider 模式，
使用 data/vision_spots.json 作为固定图库（5 个景点）。
"""

import json
import logging
from pathlib import Path

from app.providers.base import VisionProvider, VisionResult

logger = logging.getLogger(__name__)


def _load_vision_spots() -> list[dict]:
    """从 data/vision_spots.json 加载固定图库。"""
    spots_path = Path(__file__).resolve().parents[3] / "data" / "vision_spots.json"
    if spots_path.exists():
        with open(spots_path, "r", encoding="utf-8") as f:
            return json.load(f)
    logger.warning("[Vision] vision_spots.json not found, using empty gallery")
    return []


class MockVisionProvider(VisionProvider):
    """Mock 视觉：从 vision_spots.json 图库匹配景点。"""

    def __init__(self) -> None:
        self._spots = _load_vision_spots()
        logger.info("[Vision] Using Mock (no vision API key configured, %d spots in gallery)", len(self._spots))

    async def recognize(self, image_url: str, hint: str = "") -> VisionResult:
        """根据 image_url/hint 匹配 vision_spots.json 中的景点。"""
        source = f"{image_url or ''} {hint or ''}".lower()

        # 按关键词 / 图片文件名匹配
        for spot in self._spots:
            image_names = [img.lower() for img in spot.get("images", [])]
            keywords = spot.get("keywords", [])
            if any(name in source for name in image_names) or any(kw in source for kw in keywords):
                return VisionResult(
                    spot_id=spot["spotId"],
                    spot_name=spot["spotName"],
                    confidence=0.87,
                    description=spot.get("description", f"你拍到的是{spot['spotName']}。"),
                    related_spots=[{"spotId": s, "spotName": s} for s in spot.get("relatedSpots", [])],
                    visual_features=spot.get("visualFeatures", []),
                    category="spot",
                )

        # 未匹配时必须明确返回 unknown，不能伪造一个景点候选。
        return VisionResult(
            spot_id="",
            spot_name="未知",
            confidence=0.0,
            description="我还不能可靠确认图片里的对象，请补充拍摄角度或文字描述。",
            related_spots=[],
            visual_features=[],
            category="unknown",
        )
