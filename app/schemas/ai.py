from pydantic import BaseModel, Field

from app.schemas.audio import VoiceName


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
    voice: VoiceName = "guide_female"


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
    provider: str = "deepseek"


class SourceSchema(BaseModel):
    title: str
    chunkId: str


class SoloQuestionRequest(BaseModel):
    userId: str
    question: str = Field(min_length=1, max_length=2000)
    currentSpotId: str = Field(default="", max_length=100)
    needAudio: bool = True
    voice: VoiceName = "guide_female"


class SoloQuestionResponse(BaseModel):
    answer: str
    audioUrl: str | None = None
    duration: float = 0.0
    sources: list[SourceSchema] = Field(default_factory=list)
    avatarState: AvatarStateSchema
    warning: str | None = None
    mode: str = "solo"
    provider: str = "deepseek"


class VoiceQuestionRequest(BaseModel):
    roomId: str
    userId: str
    channel: str = Field(default="public", pattern="^(public|private)$")
    audioUrl: str = Field(min_length=1, max_length=14_000_000)
    audioFormat: str | None = None  # "wav" | "mp3"
    textHint: str | None = None     # 辅助识别文本
    voice: VoiceName = "guide_female"


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
    provider: str | None = None
