from pydantic import BaseModel


class RoutePreferences(BaseModel):
    interest: list[str] = []
    timeLimit: int = 60
    physicalStrength: str = "medium"
    withChildren: bool = False
    withElderly: bool = False
    avoidCrowd: bool = True


class RouteRecommendRequest(BaseModel):
    roomId: str
    userId: str
    preferences: RoutePreferences


class RouteSpotSchema(BaseModel):
    spotId: str
    spotName: str
    stayMinutes: int


class RouteRecommendResponse(BaseModel):
    routeName: str
    estimatedTime: int
    spots: list[RouteSpotSchema]
    reason: str
