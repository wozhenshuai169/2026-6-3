from pydantic import BaseModel


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
