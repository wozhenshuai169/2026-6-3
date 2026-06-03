"""ProviderFactory —— 按环境变量解析 Provider，自动 Mock 降级。"""

import logging

from app.core.config import settings
from app.providers.base import LLMProvider, VisionProvider, MapProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Provider 工厂：有 API Key 走真实实现，无 Key 降级 Mock。"""

    @staticmethod
    def get_llm() -> LLMProvider:
        if settings.llm_enabled:
            from app.providers.llm.deepseek import DeepSeekProvider
            return DeepSeekProvider()
        from app.providers.llm.mock import MockLLMProvider
        return MockLLMProvider()

    @staticmethod
    def get_vision() -> VisionProvider:
        if settings.vision_enabled:
            from app.providers.vision.qwen_vl import QwenVLVisionProvider
            return QwenVLVisionProvider()
        from app.providers.vision.mock import MockVisionProvider
        return MockVisionProvider()

    @staticmethod
    def get_map() -> MapProvider:
        if settings.map_enabled:
            # 后续接入高德 / 百度地图时在此分支
            logger.warning("[Map] Real provider not yet implemented, falling back to Mock")
        from app.providers.map.mock import MockMapProvider
        return MockMapProvider()


# 模块级单例（无状态，可安全复用）
_factory = ProviderFactory()

get_llm = _factory.get_llm
get_vision = _factory.get_vision
get_map = _factory.get_map
