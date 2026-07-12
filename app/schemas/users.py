from typing import Literal

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    userName: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    role: Literal["tourist", "guide"] = "tourist"


class RegisterResponse(BaseModel):
    userId: str
    userName: str
    token: str
    role: str
    expiresAt: int


class LoginRequest(BaseModel):
    userName: str
    password: str


class AuthResponse(RegisterResponse):
    pass


class CurrentUserResponse(BaseModel):
    userId: str
    userName: str
    role: str
