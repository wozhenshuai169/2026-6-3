from pydantic import BaseModel


class PublicQuestionRequest(BaseModel):
    roomId: str
    userId: str
    question: str


class PublicQuestionResponse(BaseModel):
    roomId: str
    answer: str
