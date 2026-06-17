from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "test_data" / "real_model_validation" / "manifest.json"


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _real_audio_configured() -> bool:
    return bool(os.getenv("DASHSCOPE_API_KEY") or os.getenv("VISION_API_KEY") or os.getenv("ALIYUN_ISI_ACCESS_KEY_ID"))


def _real_vision_configured() -> bool:
    return bool(os.getenv("DASHSCOPE_API_KEY") or os.getenv("VISION_API_KEY") or os.getenv("QWEN_VL_API_KEY"))


def _client_room() -> tuple[TestClient, dict, dict]:
    client = TestClient(app)
    user = client.post(
        "/api/auth/register",
        json={"userName": f"real-dataset-{uuid4().hex[:8]}", "password": "123456"},
    )
    assert user.status_code == 200, user.text
    room = client.post(
        "/api/rooms",
        json={
            "token": user.json()["token"],
            "roomName": "real validation dataset",
            "scenicAreaId": "area_001",
            "routeId": "classic",
        },
    )
    assert room.status_code == 200, room.text
    return client, user.json(), room.json()


def _assert_not_mock(payload: dict, section: str | None = None) -> None:
    trace = payload.get("trace", {})
    marker = trace.get(section, trace) if section else trace
    provider = marker.get("provider") or payload.get("provider")
    assert provider, payload
    assert marker.get("isMock") is False, payload
    assert "mock" not in provider.lower(), payload


def _image_data_uri(asset: str) -> str:
    path = ROOT / asset
    assert path.exists(), asset
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


@pytest.mark.skipif(not _real_vision_configured(), reason="real vision provider is not configured")
def test_real_vision_cases_from_manifest():
    manifest = _manifest()
    threshold = manifest.get("thresholds", {}).get("minVisionConfidence", 0.0)
    client, user, room = _client_room()

    for case in manifest["testGroups"]["vision"]:
        response = client.post(
            case["endpoint"],
            json={
                "roomId": room["roomId"],
                "userId": user["userId"],
                "imageUrl": _image_data_uri(case["asset"]),
            },
        )
        payload = response.json()
        assert response.status_code == 200, case["id"]
        _assert_not_mock(payload)
        assert payload["recognizedSpot"]["confidence"] >= threshold, case["id"]


@pytest.mark.skipif(not _real_audio_configured(), reason="real audio provider is not configured")
def test_real_audio_cases_from_manifest():
    manifest = _manifest()
    threshold = manifest.get("thresholds", {}).get("minAsrConfidence", 0.0)
    client, user, room = _client_room()

    for case in manifest["testGroups"]["audio"]:
        request = dict(case["request"])
        if "audioUrl" not in request:
            response = client.post(case["endpoint"], json=request)
        else:
            if not os.getenv("REAL_MODEL_AUDIO_URL"):
                pytest.skip("REAL_MODEL_AUDIO_URL is required for ASR validation.")
            request.update(
                {
                    "roomId": room["roomId"],
                    "userId": user["userId"],
                    "audioUrl": os.environ["REAL_MODEL_AUDIO_URL"],
                    "audioFormat": os.getenv("REAL_MODEL_AUDIO_FORMAT", "wav"),
                }
            )
            response = client.post(case["endpoint"], json=request)

        payload = response.json()
        assert response.status_code == 200, case["id"]
        _assert_not_mock(payload)
        if "text" in payload and payload["text"]:
            assert payload["confidence"] >= threshold, case["id"]
        if case["expected"].get("audioUrlRequired"):
            assert payload["audioUrl"], case["id"]


@pytest.mark.skipif(not _real_audio_configured() or not os.getenv("REAL_MODEL_AUDIO_URL"), reason="real voice URL is not configured")
def test_real_voice_cases_from_manifest():
    manifest = _manifest()
    client, user, room = _client_room()

    for case in manifest["testGroups"]["voice"]:
        response = client.post(
            case["endpoint"],
            json={
                "roomId": room["roomId"],
                "userId": user["userId"],
                "channel": case["request"].get("channel", "public"),
                "audioUrl": os.environ["REAL_MODEL_AUDIO_URL"],
                "audioFormat": os.getenv("REAL_MODEL_AUDIO_FORMAT", "wav"),
            },
        )
        payload = response.json()
        assert response.status_code == 200, case["id"]
        _assert_not_mock(payload, "asr")
        if settings.llm_enabled:
            _assert_not_mock(payload, "llm")
