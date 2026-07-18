from pydantic import BaseModel, Field


class RoutePreferences(BaseModel):
    interest: list[str] = Field(default_factory=list)
    timeLimit: int = Field(default=60, ge=10, le=480)
    physicalStrength: str = Field(default="medium", pattern="^(low|medium|high)$")
    withChildren: bool = False
    withElderly: bool = False
    avoidCrowd: bool = True


class RouteRecommendRequest(BaseModel):
    roomId: str
    userId: str
    preferences: RoutePreferences
    scenicAreaId: str | None = None


class RouteSpotSchema(BaseModel):
    spotId: str
    spotName: str
    stayMinutes: int
    poiId: str = ""
    amapPoiName: str = ""
    longitude: float | None = None
    latitude: float | None = None
    address: str = ""
    district: str = ""
    temporarilyClosed: bool = False
    dataSource: str = ""


class RouteRecommendResponse(BaseModel):
    routeId: str
    routeName: str
    score: float = 0.0
    estimatedTime: int
    spots: list[RouteSpotSchema]
    reason: str
    distance: float = 0.0
    difficulty: str = ""
    matchedPreferences: list[str] = Field(default_factory=list)
    scoreBreakdown: dict[str, float] = Field(default_factory=dict)
    scenicAreaId: str = ""
    scenicAreaName: str = ""
    mapProvider: str = ""
    dataSource: str = ""
    routePolyline: list[str] = Field(default_factory=list)
    instructions: list[dict] = Field(default_factory=list)
