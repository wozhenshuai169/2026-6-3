from __future__ import annotations

import os

from .data_adapter import ScenicDataAdapter
from .http_provider import load_file_base64, post_json
from .rag import ScenicRAG
from .schemas import AlgorithmRequest, VisionResult
from .text_utils import contains_any


class VisionProvider:
    endpoint = os.getenv("AI_VISION_ENDPOINT")

    def recognize(self, request: AlgorithmRequest) -> dict | None:
        if not self.endpoint:
            return None
        payload = post_json(
            self.endpoint,
            {
                "imageUrl": request.imageUrl,
                "imageBase64": load_file_base64(request.imageUrl),
                "text": request.text,
                "currentSpotId": request.state.currentSpotId,
                "currentRouteId": request.state.currentRouteId,
            },
            timeout=float(os.getenv("AI_VISION_TIMEOUT", "60")),
        )
        spot_name = payload.get("spotName") or payload.get("recognizedObject")
        if not spot_name:
            return None
        return {
            "spotId": payload.get("spotId") or _spot_id_from_name(str(spot_name)),
            "spotName": str(spot_name),
            "visualFeatures": payload.get("visualFeatures") or [],
            "relatedSpots": payload.get("relatedSpots") or [],
            "confidence": float(payload.get("confidence", 0.0)),
        }
        return None


class VisionRecognizer:
    def __init__(self, data: ScenicDataAdapter, rag: ScenicRAG, provider: VisionProvider | None = None) -> None:
        self.data = data
        self.rag = rag
        self.provider = provider or VisionProvider()

    def recognize(self, request: AlgorithmRequest) -> VisionResult:
        provider_result = self.provider.recognize(request)
        spot = provider_result or self._match_reference_library(request)
        if not spot:
            current = request.state.currentSpotId
            related = [item["spotName"] for item in self.data.vision_spots[:3]]
            current_titles = [chunk["title"] for chunk in self.data.get_spot_chunks(current)[:2]]
            return VisionResult(
                recognizedObject=None,
                spotName=None,
                confidence=0.28,
                answer="我还不能可靠确认图片里的对象。可以结合当前位置先看这些候选信息，也请补充拍摄角度或文字描述。",
                visualFeatures=[],
                relatedSpots=related + current_titles,
                recommendedAction="ask_for_more_context",
            )

        qa = self.rag.query(f"介绍{spot['spotName']}", request.state.model_copy(update={"currentSpotId": spot["spotId"]}))
        return VisionResult(
            recognizedObject=spot["spotName"],
            spotName=spot["spotName"],
            confidence=spot.get("confidence", 0.84),
            visualFeatures=spot.get("visualFeatures", []),
            answer=f"你拍到的可能是{spot['spotName']}。{qa.answer}",
            citations=qa.citations,
            relatedSpots=spot.get("relatedSpots", []),
            recommendedAction="rag_explain",
        )

    def _match_reference_library(self, request: AlgorithmRequest) -> dict | None:
        text = " ".join(part for part in [request.text, request.imageUrl or "", request.audioUrl or "", request.audioPath or ""] if part)
        lowered = text.lower()
        for spot in self.data.vision_spots:
            image_names = [image.lower() for image in spot.get("images", [])]
            keywords = spot.get("keywords", [])
            if any(image in lowered for image in image_names) or contains_any(text, keywords):
                return {
                    "spotId": spot["spotId"],
                    "spotName": spot["spotName"],
                    "visualFeatures": spot.get("visualFeatures", []),
                    "relatedSpots": spot.get("relatedSpots", []),
                    "confidence": 0.87,
                }
                break
        return None


def _spot_id_from_name(name: str) -> str:
    mapping = {
        "灵山大照壁": "lingshan_dazhaobi",
        "五明桥": "wuming_bridge",
        "佛足坛": "buddha_foot_altar",
        "五智门": "wuzhi_gate",
        "菩提大道": "bodhi_avenue",
        "九龙灌浴": "jiulong_guanyu",
        "降魔浮雕": "demon_relief",
        "阿育王柱": "ashoka_pillar",
        "百子戏弥勒": "baizi_mile",
        "祥符禅寺": "xiangfu_temple",
        "祥符寺": "xiangfu_temple",
        "灵山大佛": "lingshan_buddha",
        "佛教文化博览馆": "buddhist_museum",
        "灵山梵宫": "lingshan_palace",
        "五印坛城": "wuyin_mandala",
        "曼飞龙塔": "manfeilong_pagoda",
        "无尽意斋": "wujinyi_house",
    }
    lowered = name.lower()
    for key, value in mapping.items():
        if key.lower() in lowered:
            return value
    return "lingshan_dazhaobi"
