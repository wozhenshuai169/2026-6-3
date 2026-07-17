"""Normalize model output before it is displayed or synthesized as speech."""

from __future__ import annotations

import re


_SPEECH_PUNCTUATION = "，。！？；：、,.!?;:"
_UNSUPPORTED_SPEECH_CHARS = re.compile(
    rf"[^\w\s{re.escape(_SPEECH_PUNCTUATION)}]",
    flags=re.UNICODE,
)


def sanitize_spoken_text(value: str) -> str:
    """Keep speech-friendly text while removing Markdown and special symbols."""
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", value or "")
    text = _UNSUPPORTED_SPEECH_CHARS.sub("", text).replace("_", "")
    return re.sub(r"\s+", " ", text).strip()
