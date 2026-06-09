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
    routeId: str
    routeName: str
    score: float = 0.0
    estimatedTime: int
    spots: list[RouteSpotSchema]
    reason: str
    distance: float = 0.0
    difficulty: str = ""
    matchedPreferences: list[str] = []
    scoreBreakdown: dict[str, float] = {}
