from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audio import VoiceName


class AvatarSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["xiaoyun", "yunchuan", "tongtong"]
    outfit: Literal["modern_black", "culture_red", "outdoor_ivory"]
    imageUrl: str = Field(pattern=r"^/(assets/images|uploads/avatar)/[A-Za-z0-9._/-]+$", max_length=2048)
    voice: VoiceName
    speed: float = Field(ge=0.8, le=1.3)
    emotion: Literal["friendly", "calm", "lively"]
    lipSync: bool = True
    emotionSync: bool = True
    idleMotion: bool = True


class AvatarSettingsResponse(AvatarSettingsUpdate):
    updatedAt: int
