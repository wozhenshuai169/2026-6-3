from __future__ import annotations

import os
from pathlib import PurePath

from .schemas import ASRResult, TTSResult
from .http_provider import load_file_base64, post_json


class VoiceAdapter:
    supported_formats = {"wav", "mp3"}
    voice = "guide_female_zh"
    asr_endpoint = os.getenv("AI_ASR_ENDPOINT")
    tts_endpoint = os.getenv("AI_TTS_ENDPOINT")

    def validate_format(self, audio_format: str | None, audio_path: str | None = None, audio_url: str | None = None) -> str:
        fmt = (audio_format or self._infer_format(audio_path or audio_url or "")).lower().strip(".")
        if fmt not in self.supported_formats:
            raise ValueError("只支持 wav / mp3 音频格式")
        return fmt

    def asr(
        self,
        *,
        audio_format: str | None = None,
        audio_path: str | None = None,
        audio_url: str | None = None,
        text_hint: str | None = None,
    ) -> ASRResult:
        try:
            fmt = self.validate_format(audio_format, audio_path, audio_url)
        except ValueError as exc:
            return ASRResult(text="", confidence=0.0, format=audio_format or "unknown", success=False, error=str(exc))

        if self.asr_endpoint:
            return self._real_asr(fmt=fmt, audio_path=audio_path, audio_url=audio_url)

        return ASRResult(
            text="",
            confidence=0.0,
            format=fmt,
            success=False,
            error="语音识别服务未配置",
        )

    def tts(self, text: str, *, voice: str | None = None, audio_format: str = "mp3") -> TTSResult:
        if not text.strip():
            return TTSResult(audioUrl=None, voice=voice or self.voice, format=audio_format, success=False, error="没有可合成的文本")
        if audio_format not in self.supported_formats:
            return TTSResult(audioUrl=None, voice=voice or self.voice, format=audio_format, success=False, error="只支持 wav / mp3 音频格式")
        if self.tts_endpoint:
            return self._real_tts(text=text, voice=voice or self.voice, audio_format=audio_format)
        return TTSResult(
            audioUrl=None,
            voice=voice or self.voice,
            format=audio_format,
            durationMs=0,
            success=False,
            error="讲解语音服务未配置",
        )

    def _infer_format(self, source: str) -> str:
        suffix = PurePath(source).suffix.lower().strip(".")
        return suffix or "unknown"

    def _real_asr(self, *, fmt: str, audio_path: str | None, audio_url: str | None) -> ASRResult:
        try:
            payload = post_json(
                self.asr_endpoint or "",
                {
                    "audioPath": audio_path,
                    "audioUrl": audio_url,
                    "audioFormat": fmt,
                    "audioBase64": load_file_base64(audio_path),
                    "language": "zh-CN",
                },
                timeout=float(os.getenv("AI_ASR_TIMEOUT", "60")),
            )
            return ASRResult(
                text=str(payload.get("text") or ""),
                confidence=float(payload.get("confidence", 0.0)),
                language=str(payload.get("language") or "zh-CN"),
                format=str(payload.get("format") or fmt),
                success=bool(payload.get("success", True)),
                error=payload.get("error"),
            )
        except Exception as exc:
            return ASRResult(text="", confidence=0.0, format=fmt, success=False, error=str(exc))

    def _real_tts(self, *, text: str, voice: str, audio_format: str) -> TTSResult:
        try:
            payload = post_json(
                self.tts_endpoint or "",
                {"text": text, "voice": voice, "format": audio_format, "language": "zh-CN"},
                timeout=float(os.getenv("AI_TTS_TIMEOUT", "60")),
            )
            return TTSResult(
                audioUrl=payload.get("audioUrl") or payload.get("url"),
                voice=str(payload.get("voice") or voice),
                format=str(payload.get("format") or audio_format),
                durationMs=int(payload.get("durationMs") or payload.get("duration_ms") or 0),
                success=bool(payload.get("success", True)),
                error=payload.get("error"),
            )
        except Exception as exc:
            return TTSResult(audioUrl=None, voice=voice, format=audio_format, success=False, error=str(exc))
