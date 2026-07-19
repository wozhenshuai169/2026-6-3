from pydantic import BaseModel

from app.schemas.audio import VoiceName


class AvatarStateResponse(BaseModel):
    aiStatus: str   # "idle" | "listening" | "speaking" | "thinking" | "paused" | "resuming"
    emotion: str    # "friendly" | "neutral" | "thinking" | "surprised"
    action: str     # "idle" | "listening" | "speaking" | "thinking" | "paused" | "resuming"
    text: str
    audioUrl: str
    narrationId: str = ""
    duration: float = 0.0
    voice: VoiceName = "guide_female"
