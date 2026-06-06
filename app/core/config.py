"""应用配置 —— 通过环境变量加载，支持 Mock 降级。

所有 API Key 均为可选：未设置时对应 Provider 自动降级到 Mock。
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

    # ═══════════════════════════════════════════════════
    # 功能开关
    # ═══════════════════════════════════════════════════
    enable_asr: bool = True       # ASR 语音识别
    enable_tts: bool = True       # TTS 语音合成
    enable_vision: bool = True    # 图片识景
    enable_rag: bool = False      # RAG 知识检索（暂未实现）

    # ═══════════════════════════════════════════════════
    # 地图
    # ═══════════════════════════════════════════════════
    map_api_key: str = ""
    map_provider: str = "amap"

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
    def isi_enabled(self) -> bool:
        return bool(self.isi_access_key_id and self.isi_access_key_secret and self.isi_app_key)

    @property
    def map_enabled(self) -> bool:
        return bool(self.map_api_key)


settings = Settings()
