from pydantic import BaseModel, Field


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


class VisionRecognizeResponse(BaseModel):
    recognizedSpot: RecognizedSpotSchema
    description: str
    relatedSpots: list[RelatedSpotSchema] = []
    visualFeatures: list[str] = []
    category: str = "spot"  # "spot" | "person" | "object" | "scene" | "unknown"
    provider: str = ""
    trace: dict = Field(default_factory=dict)
