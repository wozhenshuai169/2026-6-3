import base64

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings


class RecognizedSpotSchema(BaseModel):
    spotId: str
    spotName: str
    confidence: float


class RelatedSpotSchema(BaseModel):
    spotId: str
    spotName: str


class VisionRecognizeRequest(BaseModel):
    roomId: str
    userId: str
    imageUrl: str
    currentSpotId: str = ""

    @field_validator("imageUrl")
    @classmethod
    def validate_image_url(cls, value: str) -> str:
        if value.startswith("data:image/"):
            try:
                metadata, payload = value.split(",", 1)
                if not any(metadata.startswith(f"data:image/{kind};base64") for kind in ("jpeg", "png", "webp")):
                    raise ValueError("Unsupported image format")
                decoded = base64.b64decode(payload, validate=True)
            except (ValueError, base64.binascii.Error) as exc:
                raise ValueError("Invalid base64 image") from exc
            if len(decoded) > settings.max_vision_bytes:
                raise ValueError("Image is too large")
            image_type = metadata.removeprefix("data:image/").split(";", 1)[0]
            valid_signature = {
                "jpeg": decoded.startswith(b"\xff\xd8\xff"),
                "png": decoded.startswith(b"\x89PNG\r\n\x1a\n"),
                "webp": len(decoded) >= 12 and decoded.startswith(b"RIFF") and decoded[8:12] == b"WEBP",
            }[image_type]
            if not valid_signature:
                raise ValueError("Image content does not match its declared format")
            return value
        if value.startswith("/uploads/") or value.startswith("https://"):
            return value
        raise ValueError("Image URL must be an HTTPS URL, upload path, or supported data URL")


class VisionRecognizeResponse(BaseModel):
    recognizedSpot: RecognizedSpotSchema
    description: str
    relatedSpots: list[RelatedSpotSchema] = Field(default_factory=list)
    visualFeatures: list[str] = Field(default_factory=list)
    category: str = "spot"  # "spot" | "person" | "object" | "scene" | "unknown"
    warning: str | None = None
    sources: list[dict] = Field(default_factory=list)
