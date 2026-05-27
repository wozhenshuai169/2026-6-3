from __future__ import annotations

import re


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def contains_any(text: str, keywords: list[str]) -> bool:
    normalized = normalize(text)
    return any(keyword.lower() in normalized for keyword in keywords)


def tokenize(text: str) -> set[str]:
    normalized = normalize(text)
    words = set(re.findall(r"[a-zA-Z0-9_]+", normalized))
    chinese = [char for char in normalized if "\u4e00" <= char <= "\u9fff"]
    for size in (2, 3):
        words.update("".join(chinese[i : i + size]) for i in range(max(0, len(chinese) - size + 1)))
    return {word for word in words if word}
