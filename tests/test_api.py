import io
import base64
import wave
from pathlib import Path

import pytest
from starlette.websockets import WebSocketDisconnect


def _wav_bytes() -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\x00\x00" * 80)
    return output.getvalue()


def _admin(client):
    response = client.post(
        "/api/auth/login",
        json={"userName": "admin", "password": "test-admin-secret"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_health_error_model_and_security_headers(client):
    assert client.get("/health/live").json() == {"status": "live"}
    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["database"] == "ok"
    assert ready.headers["x-content-type-options"] == "nosniff"
    assert ready.headers["x-frame-options"] == "DENY"
    assert ready.headers["x-request-id"]

    error = client.get("/api/auth/me")
    assert error.status_code == 401
    assert set(error.json()) == {"detail", "errorCode", "requestId"}
    assert error.json()["errorCode"] == "UNAUTHORIZED"


def test_account_guest_logout_and_strict_bearer(client, auth_helpers):
    user = auth_helpers["register"]()
    headers = auth_helpers["headers"](user)
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["userId"] == user["userId"]

    guest = auth_helpers["guest"]("guide")
    assert guest["role"] == "guide"

    rejected = client.post(
        "/api/rooms",
        json={
            "token": guest["token"],
            "roomName": "Body token must fail",
            "scenicAreaId": "s1",
            "routeId": "r1",
        },
    )
    assert rejected.status_code == 401

    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_room_lifecycle_membership_and_leadership(client, auth_helpers):
    guide = auth_helpers["guest"]("guide", "leader")
    tourist = auth_helpers["guest"]("tourist", "member")
    outsider = auth_helpers["guest"]("tourist", "outsider")
    headers = auth_helpers["headers"]
    room_id = auth_helpers["create_room"](guide)

    assert client.get(f"/api/rooms/{room_id}", headers=headers(outsider)).status_code == 403
    joined = client.post(f"/api/rooms/{room_id}/join", headers=headers(tourist), json={})
    assert joined.status_code == 200

    paused = client.patch(
        f"/api/rooms/{room_id}/status",
        headers=headers(guide),
        json={"status": "paused"},
    )
    assert paused.json()["status"] == "paused"
    assert client.post(
        f"/api/ai/public-question",
        headers=headers(tourist),
        json={
            "roomId": room_id,
            "userId": tourist["userId"],
            "question": "What is this place?",
            "needAudio": False,
        },
    ).status_code == 409
    assert client.post(f"/api/rooms/{room_id}/join", headers=headers(outsider), json={}).status_code == 409

    assert client.patch(
        f"/api/rooms/{room_id}/status",
        headers=headers(guide),
        json={"status": "active"},
    ).status_code == 200
    transferred = client.patch(
        f"/api/rooms/{room_id}/leader",
        headers=headers(guide),
        json={"userId": tourist["userId"]},
    )
    assert transferred.status_code == 200
    assert transferred.json()["leaderId"] == tourist["userId"]
    assert client.patch(
        f"/api/rooms/{room_id}/status",
        headers=headers(guide),
        json={"status": "ended"},
    ).status_code == 403
    assert client.patch(
        f"/api/rooms/{room_id}/status",
        headers=headers(tourist),
        json={"status": "ended"},
    ).status_code == 200
    assert client.post(
        f"/api/rooms/{room_id}/messages",
        headers=headers(tourist),
        json={"content": "too late"},
    ).status_code == 409
    assert client.patch(
        f"/api/rooms/{room_id}/status",
        headers=headers(tourist),
        json={"status": "active"},
    ).status_code == 409


def test_leave_kick_and_leader_guard(client, auth_helpers):
    guide = auth_helpers["register"]("guide", "guide")
    member = auth_helpers["register"]("tourist", "member")
    other = auth_helpers["register"]("tourist", "other")
    headers = auth_helpers["headers"]
    room_id = auth_helpers["create_room"](guide)
    for user in (member, other):
        assert client.post(f"/api/rooms/{room_id}/join", headers=headers(user), json={}).status_code == 200

    assert client.delete(f"/api/rooms/{room_id}/members/me", headers=headers(guide)).status_code == 409
    assert client.delete(
        f"/api/rooms/{room_id}/members/{member['userId']}", headers=headers(other)
    ).status_code == 403
    assert client.delete(
        f"/api/rooms/{room_id}/members/{member['userId']}", headers=headers(guide)
    ).status_code == 200
    assert client.get(f"/api/rooms/{room_id}", headers=headers(member)).status_code == 403
    assert client.delete(f"/api/rooms/{room_id}/members/me", headers=headers(other)).status_code == 200


def test_message_cursor_and_websocket_ticket_are_stable_and_single_use(client, auth_helpers):
    guide = auth_helpers["register"]("guide", "ws-guide")
    tourist = auth_helpers["register"]("tourist", "ws-tourist")
    headers = auth_helpers["headers"]
    room_id = auth_helpers["create_room"](guide)
    client.post(f"/api/rooms/{room_id}/join", headers=headers(tourist), json={})

    for index in range(5):
        response = client.post(
            f"/api/rooms/{room_id}/messages",
            headers=headers(tourist),
            json={"content": f"message-{index}"},
        )
        assert response.status_code == 200

    first = client.get(f"/api/rooms/{room_id}/messages?limit=2", headers=headers(tourist)).json()
    second = client.get(
        f"/api/rooms/{room_id}/messages?limit=2&cursor={first['nextCursor']}",
        headers=headers(tourist),
    ).json()
    first_ids = {item["id"] for item in first["messages"]}
    assert first["nextCursor"]
    assert first_ids.isdisjoint({item["id"] for item in second["messages"]})

    ticket_response = client.post(
        "/api/auth/ws-ticket", headers=headers(tourist), json={"roomId": room_id}
    )
    ticket = ticket_response.json()["ticket"]
    with client.websocket_connect(f"/ws/rooms/{room_id}?ticket={ticket}") as websocket:
        assert websocket.receive_json()["type"] == "room.connected"
        websocket.send_json({"type": "message", "content": "live-message"})
        event = websocket.receive_json()
        assert event["type"] == "room.message"
        assert event["data"]["content"] == "live-message"

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/rooms/{room_id}?ticket={ticket}") as websocket:
            websocket.receive_json()


def test_audio_upload_validates_identity_signature_and_filename(client, auth_helpers):
    guide = auth_helpers["register"]("guide", "audio-guide")
    tourist = auth_helpers["register"]("tourist", "audio-tourist")
    headers = auth_helpers["headers"]
    room_id = auth_helpers["create_room"](guide)
    client.post(f"/api/rooms/{room_id}/join", headers=headers(tourist), json={})
    form = {"roomId": room_id, "userId": tourist["userId"], "channel": "public"}

    uploaded = client.post(
        "/api/audio/upload",
        headers=headers(tourist),
        data=form,
        files={"file": ("../../voice.wav", _wav_bytes(), "audio/wav")},
    )
    assert uploaded.status_code == 200, uploaded.text
    payload = uploaded.json()
    assert payload["audioUrl"].startswith("/uploads/audio/audio_")
    assert ".." not in payload["audioUrl"]

    forged = client.post(
        "/api/audio/upload",
        headers=headers(tourist),
        data=form,
        files={"file": ("voice.wav", b"not-wave", "audio/wav")},
    )
    assert forged.status_code == 415
    spoofed = dict(form, userId=guide["userId"])
    assert client.post(
        "/api/audio/upload",
        headers=headers(tourist),
        data=spoofed,
        files={"file": ("voice.wav", _wav_bytes(), "audio/wav")},
    ).status_code == 403


def test_vision_rejects_forged_base64_and_marks_mock_mode(client, auth_helpers):
    guide = auth_helpers["register"]("guide", "vision-guide")
    tourist = auth_helpers["register"]("tourist", "vision-tourist")
    headers = auth_helpers["headers"]
    room_id = auth_helpers["create_room"](guide)
    client.post(f"/api/rooms/{room_id}/join", headers=headers(tourist), json={})
    request = {"roomId": room_id, "userId": tourist["userId"], "currentSpotId": ""}

    forged = dict(request, imageUrl="data:image/png;base64," + base64.b64encode(b"not-png").decode())
    assert client.post("/api/vision/recognize", headers=headers(tourist), json=forged).status_code == 422

    png_header = b"\x89PNG\r\n\x1a\n" + b"test-image"
    valid = dict(request, imageUrl="data:image/png;base64," + base64.b64encode(png_header).decode())
    response = client.post("/api/vision/recognize", headers=headers(tourist), json=valid)
    assert response.status_code == 200, response.text
    assert response.json()["warning"] == "Mock vision mode is active."


def test_configured_llm_failure_is_503_not_mock_success(client, auth_helpers, monkeypatch):
    from app.core.config import settings
    import app.services.ai as ai_service

    class FailingLlm:
        async def chat(self, *args, **kwargs):
            raise RuntimeError("provider unavailable")

    guide = auth_helpers["register"]("guide", "provider-guide")
    tourist = auth_helpers["register"]("tourist", "provider-tourist")
    headers = auth_helpers["headers"]
    room_id = auth_helpers["create_room"](guide)
    client.post(f"/api/rooms/{room_id}/join", headers=headers(tourist), json={})
    previous_key = settings.deepseek_api_key
    settings.deepseek_api_key = "configured-for-test"
    monkeypatch.setattr(ai_service, "get_llm", lambda: FailingLlm())
    try:
        response = client.post(
            "/api/ai/public-question",
            headers=headers(tourist),
            json={
                "roomId": room_id,
                "userId": tourist["userId"],
                "question": "provider check",
                "needAudio": False,
            },
        )
    finally:
        settings.deepseek_api_key = previous_key
    assert response.status_code == 503
    assert response.json()["errorCode"] == "LLM_UNAVAILABLE"


def test_feedback_and_dashboard_use_real_database_aggregates(client, auth_helpers):
    guide = auth_helpers["register"]("guide", "stats-guide")
    tourist = auth_helpers["register"]("tourist", "stats-tourist")
    headers = auth_helpers["headers"]
    room_id = auth_helpers["create_room"](guide)
    client.post(f"/api/rooms/{room_id}/join", headers=headers(tourist), json={})
    response = client.post(
        "/api/feedback",
        headers=headers(tourist),
        json={"roomId": room_id, "userId": tourist["userId"], "score": 4, "scene": "tour"},
    )
    assert response.status_code == 200
    admin = _admin(client)
    satisfaction = client.get(
        "/api/dashboard/satisfaction", headers=headers(admin)
    ).json()
    assert satisfaction["totalResponses"] >= 1
    assert satisfaction["distribution"]["4"] >= 1
    assert client.get("/api/dashboard/overview", headers=headers(tourist)).status_code == 403


def test_knowledge_upload_chinese_search_detail_rebuild_and_delete(client, auth_helpers):
    admin = _admin(client)
    headers = auth_helpers["headers"](admin)
    content = "钟楼始建于明代，是古城的重要地标。游客可以了解古代报时制度。".encode()
    uploaded = client.post(
        "/api/kb/upload",
        headers=headers,
        files={"file": ("history.md", content, "text/markdown")},
    )
    assert uploaded.status_code == 200, uploaded.text
    document = uploaded.json()
    assert document["status"] == "indexed"
    assert document["chunkCount"] == 1

    queried = client.post(
        "/api/kb/test-query",
        headers=headers,
        json={"query": "古代报时制度", "limit": 5},
    )
    assert queried.status_code == 200, queried.text
    assert any(item["source"] == "history.md" for item in queried.json()["results"])
    assert client.get(f"/api/kb/docs/{document['docId']}", headers=headers).status_code == 200
    rebuilt = client.post("/api/kb/rebuild", headers=headers).json()
    assert rebuilt["failed"] == 0
    assert client.delete(f"/api/kb/docs/{document['docId']}", headers=headers).status_code == 204
    assert client.get(f"/api/kb/docs/{document['docId']}", headers=headers).status_code == 404


def test_openapi_and_v4_contract(client):
    schema = client.get("/openapi.json").json()
    expected = {
        ("/api/auth/guest", "post"),
        ("/api/auth/ws-ticket", "post"),
        ("/api/audio/upload", "post"),
        ("/api/feedback", "post"),
        ("/api/rooms/{roomId}/status", "patch"),
        ("/api/rooms/{roomId}/messages", "get"),
        ("/api/rooms/{roomId}/messages", "post"),
    }
    for path, method in expected:
        assert method in schema["paths"][path]

    root = Path(__file__).resolve().parents[1]
    api_client = (root / "frontend-v4/assets/js/api-client.js").read_text(encoding="utf-8")
    landing = (root / "frontend-v4/assets/js/pages/landing.js").read_text(encoding="utf-8")
    assert "Authorization" in api_client and "Bearer" in api_client
    assert "admin123" not in landing
