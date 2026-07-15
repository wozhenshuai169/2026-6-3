"""Provider 抽象基类 —— 所有 Provider 必须实现这些接口。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


# ── 通用数据结构 ────────────────────────────────────────


@dataclass
class LLMResponse:
    content: str


@dataclass
class VisionResult:
    spot_id: str
    spot_name: str
    confidence: float
    description: str
    related_spots: list[dict] = field(default_factory=list)
    visual_features: list[str] = field(default_factory=list)  # 视觉特征标签
    category: str = "spot"  # "spot" | "person" | "object" | "scene" | "unknown"


@dataclass
class RouteResult:
    route_name: str
    estimated_time: int          # 分钟
    spots: list[dict]            # [{spotId, spotName, stayMinutes}]
    reason: str
    distance: float = 0.0        # 公里
    difficulty: str = ""         # low / medium / high
    matched_preferences: list[str] = field(default_factory=list)
    score_breakdown: dict[str, float] = field(default_factory=dict)
    route_polyline: list[str] = field(default_factory=list)
    instructions: list[dict] = field(default_factory=list)
    map_provider: str = ""
    data_source: str = ""


# ── 抽象 Provider ───────────────────────────────────────


class LLMProvider(ABC):
    """LLM 文本生成 Provider"""

    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> LLMResponse:
        """非流式对话"""
        ...

    @abstractmethod
    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        """流式对话，逐 chunk yield 文本"""
        ...


class VisionProvider(ABC):
    """视觉识景 Provider —— 根据图片识别景点"""

    @abstractmethod
    async def recognize(self, image_url: str, hint: str = "") -> VisionResult:
        ...


class MapProvider(ABC):
    """地图路线 Provider —— 根据景点列表和偏好规划路线"""

    @abstractmethod
    async def plan_route(self, spot_ids: list[str], preferences: dict) -> RouteResult:
        ...
