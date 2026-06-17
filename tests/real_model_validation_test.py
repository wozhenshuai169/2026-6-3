import base64
import mimetypes
import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.providers.factory import get_audio, get_vision, is_mock_provider, provider_name


client = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]


def _real_tests_enabled() -> None:
    if os.getenv("RUN_REAL_PROVIDER_TESTS") != "1":
        pytest.skip("Set RUN_REAL_PROVIDER_TESTS=1 to run real provider validation.")


def _require_real_audio() -> None:
    _real_tests_enabled()
    if not (settings.dashscope_enabled or settings.isi_enabled):
        pytest.skip("Set DASHSCOPE_API_KEY or ISI credentials for real audio validation.")


def _require_real_vision() -> None:
    _real_tests_enabled()
    if not settings.vision_enabled:
        pytest.skip("Set DASHSCOPE_API_KEY, VISION_API_KEY, or QWEN_VL_API_KEY for real vision validation.")


def _register() -> dict:
    response = client.post(
        "/api/auth/register",
        json={"userName": f"real-{uuid4().hex[:8]}", "password": "123456"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _create_room() -> tuple[dict, dict]:
    user = _register()
    response = client.post(
        "/api/rooms",
        json={
            "token": user["token"],
            "roomName": "real provider validation",
            "scenicAreaId": "area_001",
            "routeId": "classic",
        },
    )
    assert response.status_code == 200, response.text
    return user, response.json()


def _assert_not_mock(payload: dict, section: str | None = None) -> None:
    trace = payload.get("trace", {})
    marker = trace.get(section, trace) if section else trace
    provider = marker.get("provider") or payload.get("provider")
    assert provider, payload
    assert marker.get("isMock") is False, payload
    assert "mock" not in provider.lower(), payload


def _image_data_uri(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.exists():
        pytest.skip(f"Missing image fixture: {path}")
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _audio_case_url() -> str:
    url = os.getenv("REAL_MODEL_AUDIO_URL", "").strip()
    if not url:
        pytest.skip("Set REAL_MODEL_AUDIO_URL to a public WAV/MP3 URL for real ASR validation.")
    return url


def test_real_provider_factory_never_selects_mock_when_configured():
    _real_tests_enabled()

    if settings.dashscope_enabled or settings.isi_enabled:
        audio_provider = get_audio()
        assert not is_mock_provider(audio_provider)
        assert "mock" not in provider_name(audio_provider).lower()

    if settings.vision_enabled:
        vision_provider = get_vision()
        assert not is_mock_provider(vision_provider)
        assert "mock" not in provider_name(vision_provider).lower()


def test_real_asr_uses_main_backend_audio_endpoint():
    _require_real_audio()
    user, room = _create_room()

    response = client.post(
        "/api/audio/asr",
        json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "channel": "public",
            "audioUrl": _audio_case_url(),
            "audioFormat": os.getenv("REAL_MODEL_AUDIO_FORMAT", "wav"),
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    _assert_not_mock(payload)
    expected = os.getenv("REAL_MODEL_ASR_EXPECTED", "").strip()
    if expected:
        assert expected in payload["text"]


def test_real_tts_uses_main_backend_audio_endpoint():
    _require_real_audio()

    response = client.post(
        "/api/audio/tts",
        json={"text": "前方右侧是游客服务中心。", "voice": "guide_female", "audioFormat": "mp3"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    _assert_not_mock(payload)
    assert payload["audioUrl"]
    assert payload["duration"] > 0


def test_real_vision_uses_main_backend_recognize_endpoint():
    _require_real_vision()
    user, room = _create_room()

    response = client.post(
        "/api/vision/recognize",
        json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "imageUrl": _image_data_uri("test_data/full_path_web/images/bell_tower_web.jpg"),
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    _assert_not_mock(payload)
    assert payload["recognizedSpot"]["confidence"] >= 0


def test_real_public_voice_question_uses_main_backend_endpoint():
    _require_real_audio()
    user, room = _create_room()

    response = client.post(
        "/api/ai/public-voice-question",
        json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "channel": "public",
            "audioUrl": _audio_case_url(),
            "audioFormat": os.getenv("REAL_MODEL_AUDIO_FORMAT", "wav"),
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    _assert_not_mock(payload, "asr")
    if settings.llm_enabled:
        _assert_not_mock(payload, "llm")
