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


class VoiceQuestionResponse(BaseModel):
    asrText: str
    decision: str
    answer: str
    audioUrl: str
    resumeText: str
    resumeAudioUrl: str
    sources: list[SourceSchema] = []
