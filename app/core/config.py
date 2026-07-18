"""Application configuration loaded from environment variables.

Missing external credentials disable the corresponding feature and surface a
clear configuration error; the product never substitutes fabricated results.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # ═══════════════════════════════════════════════════
    # 模型 Key & 端点
    # ═══════════════════════════════════════════════════
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    vision_api_key: str = ""
    vision_base_url: str = ""
    vision_model: str = ""
    dashscope_api_key: str = ""
    public_base_url: str = ""
    asr_model: str = "qwen3-asr-flash"

    # ═══════════════════════════════════════════════════
    # 功能开关
    # ═══════════════════════════════════════════════════
    enable_asr: bool = True       # ASR 语音识别
    enable_tts: bool = True       # TTS 语音合成
    enable_vision: bool = True    # 图片识景
    enable_rag: bool = True       # RAG 知识检索

    # ═══════════════════════════════════════════════════
    # 地图
    # ═══════════════════════════════════════════════════
    map_api_key: str = ""
    map_provider: str = "amap"
    map_base_url: str = "https://restapi.amap.com"
    map_timeout: int = 20
    map_cache_ttl_seconds: int = 600
    map_min_request_interval_ms: int = 300

    # ═══════════════════════════════════════════════════
    # ISI（已废弃，保留兼容）
    # ═══════════════════════════════════════════════════
    isi_access_key_id: str = ""
    isi_access_key_secret: str = ""
    isi_app_key: str = ""

    # ═══════════════════════════════════════════════════
    # 运行时
    # ═══════════════════════════════════════════════════
    log_level: str = "INFO"       # DEBUG | INFO | WARNING | ERROR
    request_timeout: int = 60     # 模型请求超时（秒）
    asr_timeout: int = 90         # ASR 轮询超时（秒）
    max_retries: int = 1          # 失败重试次数

    # Authentication and browser access
    session_ttl_seconds: int = 24 * 60 * 60
    admin_user_name: str = "admin"
    admin_password: str = ""
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    database_path: str = "data/app.db"
    max_request_bytes: int = 25 * 1024 * 1024
    max_audio_upload_bytes: int = 12 * 1024 * 1024
    max_vision_bytes: int = 10 * 1024 * 1024
    ws_ticket_ttl_seconds: int = 60
    guest_ttl_seconds: int = 12 * 60 * 60
    rate_limit_enabled: bool = True

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


    # ═══════════════════════════════════════════════════
    # 派生属性
    # ═══════════════════════════════════════════════════
    @property
    def llm_enabled(self) -> bool:
        return bool(self.deepseek_api_key)

    @property
    def vision_enabled(self) -> bool:
        return (
            bool(self.vision_api_key)
            and bool(self.vision_base_url)
            and bool(self.vision_model)
            and self.enable_vision
        )

    @property
    def audio_provider_enabled(self) -> bool:
        return self.asr_provider_enabled or self.tts_provider_enabled

    @property
    def asr_provider_enabled(self) -> bool:
        return self.enable_asr and (bool(self.dashscope_api_key or self.vision_api_key) or self.isi_enabled)

    @property
    def tts_provider_enabled(self) -> bool:
        return self.enable_tts or self.isi_enabled

    @property
    def isi_enabled(self) -> bool:
        return bool(self.isi_access_key_id and self.isi_access_key_secret and self.isi_app_key)

    @property
    def map_enabled(self) -> bool:
        return bool(self.map_api_key)


settings = Settings()
