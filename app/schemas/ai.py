from pydantic import BaseModel, Field


class AvatarStateSchema(BaseModel):
    status: str
    emotion: str = "friendly"
    action: str = "answer"
    mouthOpen: bool = False


class PublicQuestionRequest(BaseModel):
    roomId: str
    userId: str
    question: str = Field(min_length=1, max_length=2000)
    needAudio: bool = True


class PublicQuestionResponse(BaseModel):
    roomId: str
    answer: str
    audioUrl: str | None = None
    duration: float = 0.0
    sources: list["SourceSchema"] = Field(default_factory=list)
    avatarState: AvatarStateSchema
    warning: str | None = None
    decision: str | None = None
    events: list[dict] = Field(default_factory=list)
    stateUpdate: dict = Field(default_factory=dict)


class SourceSchema(BaseModel):
    title: str
    chunkId: str


class VoiceQuestionRequest(BaseModel):
    roomId: str
    userId: str
    channel: str = Field(default="public", pattern="^(public|private)$")
    audioUrl: str = Field(min_length=1, max_length=14_000_000)
    audioFormat: str | None = None  # "wav" | "mp3"
    textHint: str | None = None     # 辅助识别文本


class VoiceQuestionResponse(BaseModel):
    asrText: str
    asrConfidence: float = 0.0
    decision: str
    answer: str
    audioUrl: str | None = None
    duration: float = 0.0
    resumeText: str
    resumeAudioUrl: str | None = None
    resumeDuration: float = 0.0
    sources: list[SourceSchema] = Field(default_factory=list)
    avatarState: AvatarStateSchema
    warning: str | None = None
    events: list[dict] = Field(default_factory=list)
