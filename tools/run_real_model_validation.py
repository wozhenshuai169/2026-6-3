"""Run content-driven ASR, TTS and vision checks through the product API.

This intentionally targets an already deployed backend instead of importing the
algorithm app in-process.  That is required for external ASR providers to read
the uploaded audio URL and for the result to cover authentication, persistence
and the actual API response mappers.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import httpx


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "test_data" / "real_model_validation" / "manifest.json"
REPORT = ROOT / "data" / "real_model_validation_report.json"


class ValidationFailure(RuntimeError):
    pass


def _load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _assert(condition: bool, case_id: str, message: str) -> None:
    if not condition:
        raise ValidationFailure(f"{case_id}: {message}")


def _json(response: httpx.Response, case_id: str) -> dict:
    _assert(response.status_code < 400, case_id, f"HTTP {response.status_code}: {response.text[:400]}")
    try:
        return response.json()
    except ValueError as exc:
        raise ValidationFailure(f"{case_id}: response is not JSON") from exc


def _headers(session: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {session['token']}"}


def _guest(client: httpx.Client, role: str) -> dict:
    response = client.post(
        "/api/auth/guest",
        json={"displayName": f"real-validation-{role}-{uuid4().hex[:8]}", "role": role},
    )
    return _json(response, f"bootstrap_{role}")


def _room(client: httpx.Client) -> tuple[dict, dict, str]:
    guide = _guest(client, "guide")
    tourist = _guest(client, "tourist")
    created = _json(
        client.post(
            "/api/rooms",
            headers=_headers(guide),
            json={"roomName": "Real provider validation", "scenicAreaId": "scenic_001", "routeId": "classic"},
        ),
        "create_room",
    )
    room_id = created["roomId"]
    _json(client.post(f"/api/rooms/{room_id}/join", headers=_headers(tourist), json={}), "join_room")
    return guide, tourist, room_id


def _data_url(asset: Path) -> str:
    mime = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(asset.read_bytes()).decode('ascii')}"


def _run_images(client: httpx.Client, tourist: dict, room_id: str, manifest: dict) -> list[str]:
    passed: list[str] = []
    threshold = float(manifest.get("thresholds", {}).get("minVisionConfidence", 0))
    for case in manifest["testGroups"].get("image", []):
        asset = ROOT / case["asset"]
        _assert(asset.exists(), case["id"], f"missing asset {asset}")
        payload = _json(
            client.post(
                "/api/vision/recognize",
                headers=_headers(tourist),
                json={"roomId": room_id, "userId": tourist["userId"], "imageUrl": _data_url(asset)},
            ),
            case["id"],
        )
        recognized = payload.get("recognizedSpot", {}).get("spotName", "")
        expected = case["expected"]
        _assert(
            any(candidate.casefold() in recognized.casefold() for candidate in expected["recognizedObjectAnyOf"]),
            case["id"],
            f"unexpected recognition: {recognized!r}",
        )
        _assert(payload["recognizedSpot"].get("confidence", 0) >= threshold, case["id"], "confidence below threshold")
        if expected.get("requiresCitation"):
            _assert(bool(payload.get("sources")), case["id"], "recognized image has no knowledge citation")
        passed.append(case["id"])
    return passed


def _run_text(client: httpx.Client, tourist: dict, room_id: str, manifest: dict) -> list[str]:
    """Validate the deployed LLM path, including product-side retrieval citations."""
    passed: list[str] = []
    for case in manifest["testGroups"].get("text", []):
        payload = _json(
            client.post(
                "/api/ai/public-question",
                headers=_headers(tourist),
                json={
                    "roomId": room_id, "userId": tourist["userId"],
                    "question": case["question"], "needAudio": False,
                },
            ),
            case["id"],
        )
        expected = case["expected"]
        _assert(bool(payload.get("answer", "").strip()), case["id"], "LLM returned an empty answer")
        if expected.get("requiresCitation"):
            _assert(bool(payload.get("sources")), case["id"], "answer has no knowledge citation")
        if expected.get("decision"):
            _assert(payload.get("decision") == expected["decision"], case["id"], "unexpected decision")
        passed.append(case["id"])
    return passed


def _run_voice(client: httpx.Client, tourist: dict, room_id: str, manifest: dict, skip_missing: bool) -> list[str]:
    passed: list[str] = []
    threshold = float(manifest.get("thresholds", {}).get("minAsrConfidence", 0))
    for case in manifest["testGroups"].get("voice", []):
        asset = ROOT / case["asset"]
        if not asset.exists():
            if skip_missing:
                print(f"SKIP {case['id']}: missing recording {asset}")
                continue
            raise ValidationFailure(f"{case['id']}: missing recording {asset}")
        mime = mimetypes.guess_type(asset.name)[0] or "audio/wav"
        upload = _json(
            client.post(
                "/api/audio/upload",
                headers=_headers(tourist),
                data={"roomId": room_id, "userId": tourist["userId"], "channel": case["channel"]},
                files={"file": (asset.name, asset.read_bytes(), mime)},
            ),
            f"{case['id']}_upload",
        )
        payload = _json(
            client.post(
                "/api/ai/public-voice-question",
                headers=_headers(tourist),
                json={
                    "roomId": room_id,
                    "userId": tourist["userId"],
                    "channel": case["channel"],
                    "audioUrl": upload["audioUrl"],
                    "audioFormat": upload["audioFormat"],
                },
            ),
            case["id"],
        )
        expected = case["expected"]
        _assert(
            any(candidate in payload.get("asrText", "") for candidate in expected["asrContainsAnyOf"]),
            case["id"],
            f"unexpected ASR text: {payload.get('asrText')!r}",
        )
        _assert(payload.get("decision") == expected["decision"], case["id"], "unexpected decision")
        _assert(payload.get("audioUrl"), case["id"], "TTS did not return audioUrl")
        _assert(payload.get("duration", 0) > 0, case["id"], "TTS duration is empty")
        _assert(payload.get("asrConfidence", 0) >= threshold, case["id"], "ASR confidence below threshold")
        passed.append(case["id"])
    return passed


def _run_tts(client: httpx.Client, tourist: dict, manifest: dict) -> list[str]:
    passed: list[str] = []
    for case in manifest["testGroups"].get("tts", []):
        payload = _json(
            client.post("/api/audio/tts", headers=_headers(tourist), json={"text": case["text"]}),
            case["id"],
        )
        if case["expected"].get("audioUrlRequired"):
            _assert(bool(payload.get("audioUrl")), case["id"], "TTS did not return audioUrl")
        passed.append(case["id"])
    return passed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="")
    parser.add_argument("--skip-missing-audio", action="store_true")
    parser.add_argument("--skip-tts", action="store_true")
    args = parser.parse_args()
    manifest = _load_manifest()
    base_url = (args.base_url or manifest["baseUrl"]).rstrip("/")
    try:
        with httpx.Client(base_url=base_url, timeout=90) as client:
            guide, tourist, room_id = _room(client)
            del guide
            passed = []
            passed.extend(_run_text(client, tourist, room_id, manifest))
            passed.extend(_run_images(client, tourist, room_id, manifest))
            passed.extend(_run_voice(client, tourist, room_id, manifest, args.skip_missing_audio))
            if not args.skip_tts:
                passed.extend(_run_tts(client, tourist, manifest))
    except (httpx.HTTPError, ValidationFailure) as exc:
        report = {
            "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
            "baseUrl": base_url,
            "status": "blocked",
            "passed": passed if "passed" in locals() else [],
            "skipped": {"tts": args.skip_tts, "missingAudio": args.skip_missing_audio},
            "error": str(exc),
        }
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"REAL VALIDATION FAILED: {exc}", file=sys.stderr)
        print(json.dumps(report, ensure_ascii=False), file=sys.stderr)
        return 1
    report = {
        "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "baseUrl": base_url,
        "status": "passed",
        "passed": passed,
        "count": len(passed),
        "skipped": {"tts": args.skip_tts, "missingAudio": args.skip_missing_audio},
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
