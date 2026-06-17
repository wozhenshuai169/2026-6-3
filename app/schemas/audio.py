from pydantic import BaseModel


class ASRRequest(BaseModel):
    roomId: str
    userId: str
    channel: str  # "public" | "private"
    audioUrl: str
    audioFormat: str | None = None  # "wav" | "mp3"
    textHint: str | None = None     # 辅助识别文本


class ASRResponse(BaseModel):
    text: str
    confidence: float


class AudioUploadResponse(BaseModel):
    audioUrl: str
    audioFormat: str
    size: int
    filename: str


class TTSRequest(BaseModel):
    text: str
    voice: str = "guide_female"
    speed: float = 1.0
    audioFormat: str = "mp3"  # "wav" | "mp3"


class TTSResponse(BaseModel):
    audioUrl: str
    duration: float  # seconds
