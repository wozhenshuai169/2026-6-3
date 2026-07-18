"""Resolve configured external providers without synthetic fallbacks."""

import logging
from functools import lru_cache

from app.core.config import settings
from app.providers.base import LLMProvider, VisionProvider, MapProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Provider factory: missing credentials are reported explicitly."""

    @staticmethod
    def get_llm() -> LLMProvider:
        if not settings.llm_enabled:
            raise RuntimeError("智能问答服务未配置")
        from app.providers.llm.deepseek import DeepSeekProvider
        return DeepSeekProvider()

    @staticmethod
    def get_vision() -> VisionProvider:
        if not settings.vision_enabled:
            raise RuntimeError("图片识别服务未配置")
        from app.providers.vision.qwen_vl import QwenVLVisionProvider
        return QwenVLVisionProvider()

    @staticmethod
    @lru_cache(maxsize=1)
    def get_map() -> MapProvider:
        if not settings.map_enabled:
            raise RuntimeError("MAP_API_KEY 未配置，真实地图服务不可用")
        if settings.map_provider.lower() != "amap":
            raise RuntimeError(f"不支持的地图服务：{settings.map_provider}")
        from app.providers.map.amap import AmapMapProvider

        logger.info("[Map] 使用高德 Web 服务")
        return AmapMapProvider()

    @staticmethod
    def get_audio():
        """Return the configured speech provider."""
        if settings.tts_provider_enabled or settings.dashscope_api_key or settings.vision_api_key:
            from app.providers.audio.dashscope import DashScopeAudioProvider
            logger.info("[Audio] Using Qwen-ASR + Edge TTS provider")
            return DashScopeAudioProvider()
        if settings.isi_enabled:
            from app.providers.audio.aliyun_isi import AliyunISIProvider
            logger.info("[Audio] Using Aliyun ISI provider")
            return AliyunISIProvider()
        raise RuntimeError("语音识别与合成服务未配置")


# 模块级单例（无状态，可安全复用）
_factory = ProviderFactory()

get_llm = _factory.get_llm
get_vision = _factory.get_vision
get_map = _factory.get_map
get_audio = _factory.get_audio
