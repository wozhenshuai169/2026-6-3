"""应用配置 —— 通过环境变量加载，支持 Mock 降级。

所有 API Key 均为可选：未设置时对应 Provider 自动降级到 Mock。
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # ── DeepSeek LLM ──
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # ── Vision (多模态，后续接入 Qwen-VL / GPT-4V) ──
    vision_api_key: str = ""
    vision_base_url: str = ""
    vision_model: str = ""

    # ── Map (后续接入高德 / 百度地图) ──
    map_api_key: str = ""
    map_provider: str = "amap"  # "amap" | "baidu"

    @property
    def llm_enabled(self) -> bool:
        return bool(self.deepseek_api_key)

    @property
    def vision_enabled(self) -> bool:
        return bool(self.vision_api_key and self.vision_base_url and self.vision_model)

    @property
    def map_enabled(self) -> bool:
        return bool(self.map_api_key)


settings = Settings()
