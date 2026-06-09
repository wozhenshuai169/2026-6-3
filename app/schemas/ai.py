from pydantic import BaseModel


class AvatarStateSchema(BaseModel):
    status: str
    emotion: str = "friendly"
    action: str = "answer"
    mouthOpen: bool = False


class PublicQuestionRequest(BaseModel):
    roomId: str
    userId: str
    question: str
    needAudio: bool = True


class PublicQuestionResponse(BaseModel):
    roomId: str
    answer: str
    audioUrl: str | None = None
    duration: float = 0.0
    sources: list["SourceSchema"] = []
    avatarState: AvatarStateSchema
    warning: str | None = None


class SourceSchema(BaseModel):
    title: str
    chunkId: str


class VoiceQuestionRequest(BaseModel):
    roomId: str
    userId: str
    channel: str = "public"
    audioUrl: str
    audioFormat: str | None = None  # "wav" | "mp3"
    textHint: str | None = None     # 辅助识别文本


class VoiceQuestionResponse(BaseModel):
    asrText: str
    decision: str
    answer: str
    audioUrl: str | None = None
    duration: float = 0.0
    resumeText: str
    resumeAudioUrl: str | None = None
    resumeDuration: float = 0.0
    sources: list[SourceSchema] = []
    avatarState: AvatarStateSchema
    warning: str | None = None
    events: list[dict] = []
