from pydantic import BaseModel


class RegisterRequest(BaseModel):
    userName: str
    password: str


class RegisterResponse(BaseModel):
    userId: str
    userName: str
    token: str
