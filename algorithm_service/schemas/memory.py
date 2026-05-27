from __future__ import annotations

from pydantic import BaseModel


class MemoryExtractRequest(BaseModel):
    userId: str
    dialogue: str
    context: dict = {}


class MemoryExtractResponse(BaseModel):
    tags: list[str] = []
    interests: list[str] = []
    summary: str = ""
