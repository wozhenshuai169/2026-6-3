from typing import Literal

from pydantic import BaseModel, Field


VoiceName = Literal["guide_female", "xiaomei", "guide_male", "xiaowei"]


class ASRRequest(BaseModel):
    roomId: str
    userId: str
    channel: str = Field(pattern="^(public|private)$")
    audioUrl: str = Field(min_length=1, max_length=2048)
    audioFormat: str | None = None  # "wav" | "mp3"
    textHint: str | None = None     # 辅助识别文本


class ASRResponse(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    confidence: float
    warning: str | None = None


class TTSRequest(BaseModel):
    text: str
    voice: VoiceName = "guide_female"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    audioFormat: str = "mp3"  # "wav" | "mp3"


class TTSResponse(BaseModel):
    audioUrl: str
    duration: float  # seconds
    warning: str | None = None


class AudioUploadResponse(BaseModel):
    audioUrl: str
    audioFormat: str
    size: int
