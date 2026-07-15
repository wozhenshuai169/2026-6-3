from pydantic import BaseModel


class AvatarStateResponse(BaseModel):
    aiStatus: str   # "idle" | "listening" | "speaking" | "thinking" | "paused" | "resuming"
    emotion: str    # "friendly" | "neutral" | "thinking" | "surprised"
    action: str     # "idle" | "listening" | "speaking" | "thinking" | "paused" | "resuming"
    text: str
    audioUrl: str
    narrationId: str = ""
    duration: float = 0.0
