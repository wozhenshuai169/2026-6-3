"""Scenic RAG based on the local scenic chunk corpus."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "scenic_chunks.json"

SYNONYMS = {
    "厕所": ["厕所", "卫生间", "洗手间", "restroom", "toilet"],
    "卫生间": ["厕所", "卫生间", "洗手间", "restroom", "toilet"],
    "洗手间": ["厕所", "卫生间", "洗手间", "restroom", "toilet"],
    "服务中心": ["服务中心", "游客服务中心", "咨询", "失物", "轮椅"],
    "钟楼": ["钟楼", "钟", "bell tower"],
    "鼓楼": ["鼓楼", "鼓", "drum tower"],
    "休息": ["休息", "休息区", "座椅", "饮水"],
    "无障碍": ["无障碍", "行动不便", "坡道", "轮椅"],
}

REFUSAL = "资料中没有查到可靠依据，我不能编造答案。建议咨询现场工作人员或游客服务中心。"


@lru_cache(maxsize=1)
def _chunks() -> list[dict]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _terms(text: str) -> list[str]:
    lowered = text.lower()
    words = re.findall(r"[a-z0-9]+", lowered)
    chars = [char for char in text if "\u4e00" <= char <= "\u9fff"]
    terms = words + chars
    for key, values in SYNONYMS.items():
        if key in text or any(value.lower() in lowered for value in values):
            terms.extend(value.lower() for value in values)
    return [term for term in terms if term.strip()]


def _score(chunk: dict, question: str, current_spot: str) -> float:
    haystack = " ".join(
        str(chunk.get(field, ""))
        for field in ("chunkId", "spotId", "title", "topic", "type", "source", "content")
    ).lower()
    score = 0.0
    for term in _terms(question):
        term = term.lower()
        if not term:
            continue
        if term in haystack:
            score += 3.0 if len(term) > 1 else 0.4
    if current_spot and current_spot == chunk.get("spotId"):
        score += 2.0
    if str(chunk.get("spotId", "")) in question:
        score += 2.0
    return score


def _retrieve(question: str, current_spot: str, limit: int = 4) -> list[dict]:
    ranked = sorted(
        ((_score(chunk, question, current_spot), chunk) for chunk in _chunks()),
        key=lambda item: item[0],
        reverse=True,
    )
    return [chunk for score, chunk in ranked[:limit] if score >= 2.0]


def answer(roomId: str, userId: str, question: str, currentSpot: str = "", context: dict = None) -> dict:
    _ = (roomId, userId, context)
    matches = _retrieve(question, currentSpot)
    if not matches:
        return {
            "answer": REFUSAL,
            "sources": [],
            "confidence": 0.15,
            "stateUpdate": {"rag": {"refused": True, "reason": "no_supporting_chunk"}},
        }

    snippets = []
    for chunk in matches:
        title = chunk.get("title", "")
        content = chunk.get("content", "")
        snippets.append(f"{title}: {content}")

    confidence = min(0.95, 0.55 + len(matches) * 0.1)
    return {
        "answer": "；".join(snippets),
        "sources": [f"{chunk.get('chunkId')}:{chunk.get('title')}" for chunk in matches],
        "confidence": confidence,
        "stateUpdate": {
            "rag": {
                "refused": False,
                "matchedChunkIds": [chunk.get("chunkId") for chunk in matches],
            }
        },
    }
