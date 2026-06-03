from pydantic import BaseModel


class PublicQuestionRequest(BaseModel):
    roomId: str
    userId: str
    question: str


class PublicQuestionResponse(BaseModel):
    roomId: str
    answer: str


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
    audioUrl: str
    resumeText: str
    resumeAudioUrl: str
    sources: list[SourceSchema] = []
    events: list[dict] = []
