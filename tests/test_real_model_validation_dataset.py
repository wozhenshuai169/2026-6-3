from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "test_data" / "real_model_validation" / "manifest.json"


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _real_audio_configured() -> bool:
    return bool(os.getenv("DASHSCOPE_API_KEY") or os.getenv("ALIYUN_ISI_ACCESS_KEY_ID"))


def _real_vision_configured() -> bool:
    return bool(os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_VL_API_KEY"))


@pytest.mark.skipif(not _real_vision_configured(), reason="real vision provider is not configured")
def test_real_vision_cases_from_manifest():
    client = TestClient(app)
    manifest = _manifest()
    threshold = manifest.get("thresholds", {}).get("minVisionConfidence", 0.0)
    for case in manifest["testGroups"]["image"]:
        asset = ROOT / case["asset"]
        assert asset.exists(), case["id"]

        response = client.post(case["endpoint"], json=case["request"])
        payload = response.json()
        assert response.status_code == 200, case["id"]
        assert payload["decision"]["decision"] == case["expected"]["decision"], case["id"]
        vision = payload["vision"]
        recognized = vision["recognizedObject"] or vision["spotName"] or ""
        assert any(candidate.lower() in recognized.lower() for candidate in case["expected"]["recognizedObjectAnyOf"]), case["id"]
        assert vision["confidence"] >= threshold, case["id"]


@pytest.mark.skipif(not _real_audio_configured(), reason="real ASR/TTS provider is not configured")
def test_real_voice_cases_from_manifest():
    client = TestClient(app)
    manifest = _manifest()
    threshold = manifest.get("thresholds", {}).get("minAsrConfidence", 0.0)
    for case in manifest["testGroups"]["voice"]:
        asset = ROOT / case["asset"]
        assert asset.exists(), f"{case['id']} missing recording for: {case.get('recordingText', '')}"

        response = client.post(case["endpoint"], json=case["request"])
        payload = response.json()
        assert response.status_code == 200, case["id"]
        asr = payload["asr"]
        assert any(candidate in asr["text"] for candidate in case["expected"]["asrContainsAnyOf"]), case["id"]
        assert asr["confidence"] >= threshold, case["id"]
        assert payload["algorithm"]["decision"]["decision"] == case["expected"]["decision"], case["id"]
        assert payload["tts"]["success"] is case["expected"]["ttsSuccess"], case["id"]
        assert payload["tts"]["audioUrl"], case["id"]


@pytest.mark.skipif(not _real_audio_configured(), reason="real TTS provider is not configured")
def test_real_tts_cases_from_manifest():
    client = TestClient(app)
    manifest = _manifest()
    for case in manifest["testGroups"]["tts"]:
        response = client.post(case["endpoint"], json=case["request"])
        payload = response.json()
        assert response.status_code == 200, case["id"]
        assert payload["success"] is case["expected"]["success"], case["id"]
        if case["expected"].get("audioUrlRequired"):
            assert payload["audioUrl"], case["id"]
