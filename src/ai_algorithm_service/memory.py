from __future__ import annotations

from .text_utils import contains_any


class MemoryExtractor:
    def extract(self, text: str) -> dict:
        tags: dict[str, list[str] | str] = {}
        if contains_any(text, ["孩子", "小孩", "儿童"]):
            tags.setdefault("companions", []).append("child")
        if contains_any(text, ["老人", "长辈", "腿脚"]):
            tags.setdefault("companions", []).append("elderly")
        if contains_any(text, ["走不动", "累", "少走路", "休息"]):
            tags["stamina"] = "low"
            tags.setdefault("routePreference", []).append("less_walking")
        if contains_any(text, ["建筑", "屋顶", "工艺", "历史", "文物"]):
            tags.setdefault("interest", []).append("architecture" if "建筑" in text or "屋顶" in text else "history")
        if contains_any(text, ["英文", "英语"]):
            tags["language"] = "en-US"
        elif text:
            tags["language"] = "zh-CN"
        return tags

