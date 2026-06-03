from pydantic import BaseModel


class ASRRequest(BaseModel):
    roomId: str
    userId: str
    channel: str  # "public" | "private"
    audioUrl: str


class ASRResponse(BaseModel):
    text: str
    confidence: float


class TTSRequest(BaseModel):
    text: str
    voice: str = "guide_female"
    speed: float = 1.0


class TTSResponse(BaseModel):
    audioUrl: str
    duration: float  # seconds
