import io
import base64
import json
import re
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


@pytest.fixture
def fake_deepseek(monkeypatch):
    from types import SimpleNamespace

    from app.core.config import settings
    import app.services.ai as ai_service

    calls = []

    class FakeDeepSeek:
        async def chat(self, messages, **kwargs):
            calls.append({"messages": messages, "kwargs": kwargs})
            return SimpleNamespace(content="我是云游智导的导览助手，可以为你介绍景点和游览信息。")

    previous_key = settings.deepseek_api_key
    settings.deepseek_api_key = "configured-for-test"
    monkeypatch.setattr(ai_service, "get_llm", lambda: FakeDeepSeek())
    try:
        yield calls
    finally:
        settings.deepseek_api_key = previous_key


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


def test_tts_rejects_missing_provider_file_without_creating_demo(monkeypatch):
    import asyncio
    from uuid import uuid4

    from app.core.config import settings
    import app.services.audio as audio_service

    missing_name = f"missing-{uuid4().hex}.mp3"
    missing_url = f"/uploads/tts/{missing_name}"

    class MissingFileAudio:
        async def tts_synthesize(self, **kwargs):
            return {
                "audioUrl": missing_url,
                "duration": 2.0,
                "voice": kwargs["voice"],
                "format": "mp3",
                "success": True,
            }

    previous_tts = settings.enable_tts
    previous_key = settings.dashscope_api_key
    settings.enable_tts = True
    settings.dashscope_api_key = "configured-for-test"
    monkeypatch.setattr(audio_service, "get_audio", lambda: MissingFileAudio())
    try:
        result = asyncio.run(audio_service.tts_synthesize("测试讲解", room_id="test-room"))
    finally:
        settings.enable_tts = previous_tts
        settings.dashscope_api_key = previous_key

    assert result["success"] is False
    assert result["audioUrl"] == ""
    assert result["error"] == "讲解语音文件生成失败"
    assert not (audio_service.UPLOADS_TTS_DIR / missing_name).exists()


def test_vision_rejects_forged_base64_without_calling_external_service(
    client, auth_helpers, monkeypatch
):
    import app.api.vision as vision_api

    async def fixed_recognition(*args, **kwargs):
        return {
            "recognizedSpot": {
                "spotId": "lingshan_buddha",
                "spotName": "灵山大佛",
                "confidence": 0.9,
            },
            "description": "识别输入已通过接口校验。",
            "relatedSpots": [],
            "visualFeatures": ["景区建筑"],
            "category": "spot",
            "warning": None,
            "sources": [],
        }

    monkeypatch.setattr(vision_api, "recognize_image", fixed_recognition)
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
    assert response.json()["warning"] is None


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
    client.post(
        f"/api/rooms/{room_id}/current-spot",
        headers=headers(guide),
        json={"spotId": "lingshan_dazhaobi"},
    )
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
                "question": "这里有什么历史？",
                "needAudio": False,
            },
        )
    finally:
        settings.deepseek_api_key = previous_key
    assert response.status_code == 503
    assert response.json()["errorCode"] == "LLM_UNAVAILABLE"


def test_solo_question_uses_deepseek_without_a_room(client, auth_helpers, monkeypatch):
    from types import SimpleNamespace

    from app.core.config import settings
    import app.services.ai as ai_service

    calls = []

    class FakeDeepSeek:
        async def chat(self, messages, **kwargs):
            calls.append({"messages": messages, "kwargs": kwargs})
            return SimpleNamespace(content="前方有休息需求时，请先在附近设施中查看实时服务点。")

    async def fake_tts(text, voice="guide_female", speed=1.0, room_id=None):
        assert room_id is None
        assert voice == "xiaomei"
        return {
            "success": True,
            "audioUrl": "/uploads/audio/solo-test.wav",
            "duration": 1.25,
            "warning": None,
        }

    tourist = auth_helpers["register"]("tourist", "solo-tourist")
    headers = auth_helpers["headers"]
    previous_key = settings.deepseek_api_key
    settings.deepseek_api_key = "configured-for-test"
    monkeypatch.setattr(ai_service, "get_llm", lambda: FakeDeepSeek())
    monkeypatch.setattr(ai_service, "tts_synthesize", fake_tts)
    monkeypatch.setattr(ai_service, "search_knowledge", lambda *args, **kwargs: [])
    try:
        response = client.post(
            "/api/ai/solo-question",
            headers=headers(tourist),
            json={
                "userId": tourist["userId"],
                "question": "附近有休息区吗？",
                "currentSpotId": "lingshan_dazhaobi",
                "needAudio": True,
                "voice": "xiaomei",
            },
        )
    finally:
        settings.deepseek_api_key = previous_key

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["provider"] == "deepseek"
    assert payload["mode"] == "solo"
    assert payload["audioUrl"] == "/uploads/audio/solo-test.wav"
    assert calls and calls[0]["messages"][-1]["content"] == "附近有休息区吗？"
    assert calls[0]["kwargs"]["context"]["mode"] == "solo"
    solo_prompt = calls[0]["messages"][0]["content"]
    assert "不得冒充真人" in solo_prompt
    assert "专业中文 AI" not in solo_prompt


def test_solo_question_never_falls_back_to_mock(client, auth_helpers, monkeypatch):
    from app.core.config import settings
    import app.services.ai as ai_service

    tourist = auth_helpers["register"]("tourist", "solo-no-key")
    previous_key = settings.deepseek_api_key
    settings.deepseek_api_key = ""
    monkeypatch.setattr(
        ai_service,
        "get_llm",
        lambda: (_ for _ in ()).throw(AssertionError("mock provider must not be used")),
    )
    try:
        response = client.post(
            "/api/ai/solo-question",
            headers=auth_helpers["headers"](tourist),
            json={
                "userId": tourist["userId"],
                "question": "介绍一下当前景点",
                "needAudio": False,
            },
        )
    finally:
        settings.deepseek_api_key = previous_key

    assert response.status_code == 503
    assert response.json()["errorCode"] == "LLM_NOT_CONFIGURED"


def test_guide_start_narration_generates_audio_for_room_members(client, auth_helpers, monkeypatch):
    from types import SimpleNamespace

    from app.core.config import settings
    import app.services.narration as narration_service

    class FakeDeepSeek:
        async def chat(self, messages, **kwargs):
            assert "灵山大佛" in messages[0]["content"]
            assert "现场讲解员的口吻" in messages[0]["content"]
            assert "现场中文数字导游" not in messages[0]["content"]
            return SimpleNamespace(content="各位游客，欢迎来到灵山大佛前，请放慢脚步欣赏庄严的佛教文化景观。")

    async def fake_tts(text, voice="guide_female", speed=1.0, room_id=None):
        assert room_id
        assert text.startswith("各位游客")
        assert voice == "guide_male"
        return {
            "success": True,
            "audioUrl": "/uploads/tts/room-narration-test.mp3",
            "duration": 6.5,
            "warning": None,
        }

    guide = auth_helpers["register"]("guide", "narration-guide")
    tourist = auth_helpers["register"]("tourist", "narration-tourist")
    headers = auth_helpers["headers"]
    room_id = auth_helpers["create_room"](guide)
    client.post(f"/api/rooms/{room_id}/join", headers=headers(tourist), json={})

    previous_deepseek = settings.deepseek_api_key
    previous_vision = settings.vision_api_key
    settings.deepseek_api_key = "configured-for-test"
    settings.vision_api_key = "configured-for-test"
    monkeypatch.setattr(narration_service, "get_llm", lambda: FakeDeepSeek())
    monkeypatch.setattr(narration_service, "tts_synthesize", fake_tts)
    monkeypatch.setattr(narration_service, "search_knowledge", lambda *args, **kwargs: [])
    try:
        before_start = client.get(
            f"/api/rooms/{room_id}/avatar-state",
            headers=headers(tourist),
        )
        response = client.post(
            f"/api/rooms/{room_id}/narration/start",
            headers=headers(guide),
            json={"spotId": "lingshan_buddha", "voice": "guide_male"},
        )
        forbidden = client.post(
            f"/api/rooms/{room_id}/narration/start",
            headers=headers(tourist),
            json={"spotId": "lingshan_buddha"},
        )
        avatar = client.get(
            f"/api/rooms/{room_id}/avatar-state",
            headers=headers(tourist),
        )
    finally:
        settings.deepseek_api_key = previous_deepseek
        settings.vision_api_key = previous_vision

    assert response.status_code == 200, response.text
    assert before_start.status_code == 200
    assert before_start.json()["aiStatus"] == "idle"
    assert before_start.json()["audioUrl"] == ""
    assert "等待团长" in before_start.json()["text"]
    payload = response.json()
    assert payload["llmProvider"] == "deepseek"
    assert payload["voice"] == "guide_male"
    assert payload["audioUrl"] == "/uploads/tts/room-narration-test.mp3"
    assert payload["narrationId"]
    assert forbidden.status_code == 403
    assert avatar.status_code == 200
    assert avatar.json()["narrationId"] == payload["narrationId"]
    assert avatar.json()["audioUrl"] == payload["audioUrl"]


def test_feedback_and_dashboard_use_real_database_aggregates(client, auth_helpers):
    guide = auth_helpers["register"]("guide", "stats-guide")
    tourist = auth_helpers["register"]("tourist", "stats-tourist")
    second_tourist = auth_helpers["register"]("tourist", "stats-tourist-two")
    headers = auth_helpers["headers"]
    room_id = auth_helpers["create_room"](guide)
    for user in (tourist, second_tourist):
        client.post(f"/api/rooms/{room_id}/join", headers=headers(user), json={})
        response = client.post(
            "/api/feedback",
            headers=headers(user),
            json={
                "roomId": room_id,
                "userId": user["userId"],
                "score": 2,
                "scene": "tour",
                "comment": "语音太快，有些内容听不清",
                "tags": ["语音体验"],
            },
        )
        assert response.status_code == 200
        assert response.json()["emotion"] == "negative"
    admin = _admin(client)
    satisfaction = client.get(
        "/api/dashboard/satisfaction", headers=headers(admin)
    ).json()
    assert satisfaction["totalResponses"] >= 2
    assert satisfaction["distribution"]["2"] >= 2
    assert satisfaction["emotion"]["negative"] >= 2
    assert len(satisfaction["trend"]) == 7
    report = client.get("/api/dashboard/visitor-report", headers=headers(admin)).json()
    assert any(item["topic"] == "语音体验" for item in report["attentionTopics"])
    assert any("语音体验" in item for item in report["serviceSuggestions"])
    metrics = client.get("/api/dashboard/system-metrics", headers=headers(admin)).json()
    assert {"p50LatencyMs", "p95LatencyMs", "under5SecondsRate"} <= set(metrics)
    assert client.get("/api/dashboard/overview", headers=headers(tourist)).status_code == 403


def test_avatar_settings_are_server_persisted_and_admin_controlled(client, auth_helpers):
    original = client.get("/api/avatar-settings")
    assert original.status_code == 200
    original_data = original.json()
    tourist = auth_helpers["register"]("tourist", "avatar-tourist")
    admin = _admin(client)
    payload = {
        "role": "yunchuan",
        "outfit": "culture_red",
        "imageUrl": "/assets/images/digital-guide-main.webp",
        "voice": "guide_male",
        "speed": 1.2,
        "emotion": "calm",
        "lipSync": True,
        "emotionSync": True,
        "idleMotion": False,
    }
    assert client.put(
        "/api/avatar-settings", headers=auth_helpers["headers"](tourist), json=payload
    ).status_code == 403
    saved = client.put(
        "/api/avatar-settings", headers=auth_helpers["headers"](admin), json=payload
    )
    assert saved.status_code == 200, saved.text
    assert client.get("/api/avatar-settings").json()["voice"] == "guide_male"
    restore = {key: original_data[key] for key in payload}
    assert client.put(
        "/api/avatar-settings", headers=auth_helpers["headers"](admin), json=restore
    ).status_code == 200


def test_route_template_selection_respects_interest_and_companions():
    from app.services.scenic_map import _select_route_template, get_scenic_area

    area = get_scenic_area("lingshan_shengjing")
    assert _select_route_template(area, {"timeLimit": 180, "interest": ["history"]})["routeId"] == "lingshan_history"
    assert _select_route_template(area, {"timeLimit": 180, "interest": ["nature"]})["routeId"] == "lingshan_nature"
    assert _select_route_template(area, {"timeLimit": 180, "withChildren": True})["routeId"] == "lingshan_family"
    assert _select_route_template(
        area,
        {"timeLimit": 180, "physicalStrength": "low", "withElderly": True},
    )["routeId"] == "lingshan_easy"


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


def test_lingshan_spot_knowledge_supports_route_spot_ids(client):
    response = client.get("/api/spots/lingshan_dazhaobi")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["spotName"] == "灵山大照壁"
    assert payload["scenicAreaName"] == "灵山胜境"
    assert payload["description"]
    assert isinstance(payload["chunks"], list)


def test_scenic_seed_replaces_legacy_builtin_chunks_and_preserves_uploads(tmp_path):
    from app.core.config import settings
    from app.core.database import database, reset_database_initialization_for_tests
    from app.services.knowledge import seed_scenic_chunks

    previous_path = settings.database_path
    settings.database_path = str(tmp_path / "knowledge-sync.db")
    reset_database_initialization_for_tests()
    try:
        with database() as connection:
            connection.execute(
                """
                INSERT INTO kb_documents (
                    doc_id, original_name, file_name, file_url, suffix, size, status, uploaded_at
                ) VALUES ('uploaded-doc', '管理员资料.md', 'uploaded-doc.md',
                          '/uploads/kb/uploaded-doc.md', '.md', 12, 'indexed', 1)
                """
            )
            rows = [
                ("legacy-demo", None, "旧主展厅", "旧示例资料"),
                ("uploaded-001", "uploaded-doc", "管理员补充", "管理员上传内容"),
            ]
            for chunk_id, doc_id, title, content in rows:
                connection.execute(
                    """
                    INSERT INTO kb_chunks (
                        chunk_id, doc_id, title, source, content, created_at
                    ) VALUES (?, ?, ?, '测试', ?, 1)
                    """,
                    (chunk_id, doc_id, title, content),
                )
                connection.execute(
                    "INSERT INTO kb_chunks_fts (chunk_id, title, content, source) VALUES (?, ?, ?, '测试')",
                    (chunk_id, title, content),
                )

        seed_scenic_chunks()

        with database() as connection:
            assert connection.execute(
                "SELECT 1 FROM kb_chunks WHERE chunk_id = 'legacy-demo'"
            ).fetchone() is None
            assert connection.execute(
                "SELECT 1 FROM kb_chunks_fts WHERE chunk_id = 'legacy-demo'"
            ).fetchone() is None
            assert connection.execute(
                "SELECT content FROM kb_chunks WHERE chunk_id = 'uploaded-001'"
            ).fetchone()["content"] == "管理员上传内容"
            built_in_count = connection.execute(
                "SELECT COUNT(*) AS total FROM kb_chunks WHERE doc_id IS NULL"
            ).fetchone()["total"]
            expected_count = len(
                json.loads((Path(__file__).resolve().parents[1] / "data/scenic_chunks.json").read_text(encoding="utf-8"))
            )
            assert built_in_count == expected_count
    finally:
        settings.database_path = previous_path
        reset_database_initialization_for_tests()


def test_openapi_and_v4_contract(client):
    root_response = client.get("/", follow_redirects=False)
    assert root_response.status_code == 307
    assert root_response.headers["location"] == "/pages/landing/index.html"

    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "云游智导景区导览服务"
    expected = {
        ("/api/auth/guest", "post"),
        ("/api/auth/ws-ticket", "post"),
        ("/api/ai/solo-question", "post"),
        ("/api/audio/upload", "post"),
        ("/api/rooms/{roomId}/narration/start", "post"),
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
    guide_html = (root / "frontend-v4/pages/guide-panel/index.html").read_text(encoding="utf-8")
    guide_script = (root / "frontend-v4/assets/js/pages/guide-panel.js").read_text(encoding="utf-8")
    landing_html = (root / "frontend-v4/pages/landing/index.html").read_text(encoding="utf-8")
    visitor_html = (root / "frontend-v4/pages/user-portal/index.html").read_text(encoding="utf-8")
    visitor_script = (root / "frontend-v4/assets/js/pages/user-portal.js").read_text(encoding="utf-8")
    assert "Authorization" in api_client and "Bearer" in api_client
    assert "admin123" not in landing
    assert 'id="btn-notifications"' in guide_html
    assert 'id="btn-more"' in guide_html
    assert 'data-more-action="refresh"' in guide_html
    assert 'id="guide-audio-seek"' in guide_html
    assert 'id="narration-voice"' in guide_html
    assert 'type="range"' in guide_html
    assert "voice: voice" in guide_script
    assert "handleAudioSeek" in guide_script
    assert "showNotificationCenter" in guide_script
    assert "handleMoreAction" in guide_script
    assert "各位朋友，欢迎来到主展厅" not in guide_html
    assert "根据当前景点资料准备讲解并播放" in guide_html
    assert 'id="modal-voice"' in landing_html
    assert 'id="room-voice-select"' in visitor_html
    assert 'id="visitor-voice"' in visitor_html
    assert visitor_html.count('../vision/index.html') == 1
    assert visitor_html.count('../recommend/index.html') == 1
    assert 'class="stage-tools"' not in visitor_html
    assert 'id="btn-switch-text" class="avatar-text-switch"' in visitor_html
    assert 'id="fn-audio"' not in visitor_html
    assert "voice:selectedVoice" in visitor_script
    assert "playRoomNarration" in visitor_script
    assert "sendPublicQuestion(text,'voice'" in visitor_script
    assert "inputMode:inputMode" in visitor_script
    assert "type==='audio'" not in visitor_script
    assert "renderKnowledgeResult" in visitor_script
    assert "正在读取当前景点资料" in visitor_script
    assert "灵山胜境周边" in visitor_script
    assert "高德真实 POI" not in visitor_script
    assert "不使用 Mock" not in visitor_script
    assert " · POI " not in visitor_script

    natural_ui_files = [
        (root / "frontend-v4/index.html").read_text(encoding="utf-8"),
        api_client,
        (root / "frontend-v4/assets/js/components.js").read_text(encoding="utf-8"),
        landing_html,
        guide_html,
        guide_script,
        visitor_html,
        visitor_script,
        (root / "frontend-v4/pages/ai-assistant/index.html").read_text(encoding="utf-8"),
        (root / "frontend-v4/assets/js/pages/ai-assistant.js").read_text(encoding="utf-8"),
        (root / "frontend-v4/pages/vision/index.html").read_text(encoding="utf-8"),
        (root / "frontend-v4/assets/js/pages/vision.js").read_text(encoding="utf-8"),
        (root / "frontend-v4/pages/recommend/index.html").read_text(encoding="utf-8"),
        (root / "frontend-v4/assets/js/pages/recommend.js").read_text(encoding="utf-8"),
        (root / "frontend-v4/pages/dashboard/index.html").read_text(encoding="utf-8"),
        (root / "frontend-v4/pages/knowledge-base/index.html").read_text(encoding="utf-8"),
        (root / "frontend-v4/pages/avatar-studio/index.html").read_text(encoding="utf-8"),
    ]
    forbidden_ui_phrases = [
        "AI 正在思考",
        "AI 正在讲解",
        "AI 实时生成",
        "高德真实",
        "不使用 Mock",
        "Key 不会发送到浏览器",
        "置信度：",
        "94.2%",
        "4.8 / 5",
        "数字人引擎在线",
        "高于赛题目标",
        "检测到你可能需要帮助",
        "请确认后端已启动",
    ]
    visible_ui = "\n".join(natural_ui_files)
    for phrase in forbidden_ui_phrases:
        assert phrase not in visible_ui

    ai_service = (root / "app/services/ai.py").read_text(encoding="utf-8")
    narration_service = (root / "app/services/narration.py").read_text(encoding="utf-8")
    vision_provider = (root / "app/providers/vision/qwen_vl.py").read_text(encoding="utf-8")
    vision_service = (root / "app/services/vision.py").read_text(encoding="utf-8")
    audio_service = (root / "app/services/audio.py").read_text(encoding="utf-8")
    assert "不得冒充真人" in ai_service
    assert "专业中文 AI 导游" not in ai_service
    assert "专业中文 AI 独自导览助手" not in ai_service
    assert "现场中文数字导游" not in narration_service
    assert "智能图片识别助手" not in vision_provider
    assert "Mock vision mode is active." not in vision_service
    assert "_write_demo_wav" not in audio_service
    assert "Mock audio mode is active." not in audio_service

    html_paths = [
        root / "frontend-v4/index.html",
        root / "frontend-v4/pages/landing/index.html",
        root / "frontend-v4/pages/guide-panel/index.html",
        root / "frontend-v4/pages/user-portal/index.html",
        root / "frontend-v4/pages/ai-assistant/index.html",
        root / "frontend-v4/pages/vision/index.html",
        root / "frontend-v4/pages/recommend/index.html",
        root / "frontend-v4/pages/dashboard/index.html",
        root / "frontend-v4/pages/knowledge-base/index.html",
        root / "frontend-v4/pages/avatar-studio/index.html",
    ]
    for path in html_paths:
        html = path.read_text(encoding="utf-8")
        ids = re.findall(r'id="([^"]+)"', html)
        assert len(ids) == len(set(ids))


def test_real_validation_manifest_targets_product_api_contract():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(
        (root / "test_data" / "real_model_validation" / "manifest.json").read_text(encoding="utf-8")
    )
    runner = root / "tools" / "run_real_model_validation.py"
    assert manifest["version"] == 2
    assert runner.exists()
    assert all("endpoint" not in case for group in manifest["testGroups"].values() for case in group)


def test_public_question_no_action_still_uses_deepseek(client, auth_helpers, fake_deepseek):
    guide = auth_helpers["register"]("guide", "public-ai-guide")
    tourist = auth_helpers["register"]("tourist", "public-ai-tourist")
    headers = auth_helpers["headers"]
    room_id = auth_helpers["create_room"](guide)
    client.post(f"/api/rooms/{room_id}/join", headers=headers(tourist), json={})

    response = client.post(
        "/api/ai/public-question",
        headers=headers(tourist),
        json={
            "roomId": room_id,
            "userId": tourist["userId"],
            "question": "你是谁？",
            "needAudio": False,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["provider"] == "deepseek"
    assert response.json()["answer"] == "我是云游智导的导览助手，可以为你介绍景点和游览信息。"
    assert fake_deepseek
    assert fake_deepseek[0]["messages"][-1]["content"] == "你是谁？"
    identity_prompt = fake_deepseek[0]["messages"][0]["content"]
    assert "不得冒充真人" in identity_prompt
    assert "专业中文 AI" not in identity_prompt


def test_browser_recognized_voice_uses_ai_without_audio_upload_and_is_counted(
    client, auth_helpers, fake_deepseek
):
    guide = auth_helpers["register"]("guide", "browser-voice-guide")
    tourist = auth_helpers["register"]("tourist", "browser-voice-tourist")
    headers = auth_helpers["headers"]
    room_id = auth_helpers["create_room"](guide)
    client.post(f"/api/rooms/{room_id}/join", headers=headers(tourist), json={})
    admin = _admin(client)
    before = client.get("/api/dashboard/overview", headers=headers(admin)).json()

    public_response = client.post(
        "/api/ai/public-question",
        headers=headers(tourist),
        json={
            "roomId": room_id,
            "userId": tourist["userId"],
            "question": "灵山大佛有多高？",
            "needAudio": False,
            "inputMode": "voice",
            "asrConfidence": 0.92,
        },
    )
    solo_response = client.post(
        "/api/ai/solo-question",
        headers=headers(tourist),
        json={
            "userId": tourist["userId"],
            "question": "九龙灌浴讲的是什么？",
            "currentSpotId": "jiulong_guanyu",
            "needAudio": False,
            "inputMode": "voice",
            "asrConfidence": 0.88,
        },
    )

    assert public_response.status_code == 200, public_response.text
    assert solo_response.status_code == 200, solo_response.text
    assert public_response.json()["provider"] == "deepseek"
    assert solo_response.json()["provider"] == "deepseek"
    after = client.get("/api/dashboard/overview", headers=headers(admin)).json()
    assert after["voiceQuestionCount"] == before["voiceQuestionCount"] + 2
    assert after["questionCount"] == before["questionCount"]


def test_unified_algorithm_private_need_is_not_persisted_publicly(client, auth_helpers, fake_deepseek):
    from app.services.users import get_user_memory_tags

    guide = auth_helpers["register"]("guide", "unified-guide")
    tourist = auth_helpers["register"]("tourist", "unified-tourist")
    headers = auth_helpers["headers"]
    room_id = auth_helpers["create_room"](guide)
    client.post(f"/api/rooms/{room_id}/join", headers=headers(tourist), json={})
    before = client.get(f"/api/rooms/{room_id}/messages", headers=headers(tourist)).json()["messages"]

    response = client.post(
        "/api/ai/public-question",
        headers=headers(tourist),
        json={
            "roomId": room_id,
            "userId": tourist["userId"],
            "question": "老人走不动了，附近可以休息吗？",
            "needAudio": False,
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["decision"] == "private_reply"
    assert payload["provider"] == "deepseek"
    assert fake_deepseek
    assert any(event["type"] == "suggest_private_channel" for event in payload["events"])
    after = client.get(f"/api/rooms/{room_id}/messages", headers=headers(tourist)).json()["messages"]
    assert len(after) == len(before)
    memory = get_user_memory_tags(tourist["userId"])
    assert memory["stamina"] == "low"
    assert "elderly" in memory["companions"]


def test_unified_algorithm_voice_clarification_and_route_score(client, auth_helpers):
    guide = auth_helpers["register"]("guide", "unified-route-guide")
    tourist = auth_helpers["register"]("tourist", "unified-route-tourist")
    headers = auth_helpers["headers"]
    room_id = auth_helpers["create_room"](guide)
    client.post(f"/api/rooms/{room_id}/join", headers=headers(tourist), json={})

    voice = client.post(
        "/api/ai/public-voice-question",
        headers=headers(tourist),
        json={
            "roomId": room_id,
            "userId": tourist["userId"],
            "channel": "public",
            "audioUrl": "https://example.com/audio/unclear.wav",
            "audioFormat": "wav",
        },
    )
    assert voice.status_code == 200, voice.text
    assert voice.json()["decision"] == "ask_clarification"

    route = client.post(
        "/api/recommend/route",
        headers=headers(tourist),
        json={
            "roomId": room_id,
            "userId": tourist["userId"],
            "preferences": {
                "interest": ["历史"],
                "timeLimit": 40,
                "physicalStrength": "low",
                "withChildren": False,
                "withElderly": True,
                "avoidCrowd": True,
            },
        },
    )
    assert route.status_code == 200, route.text
    recommendation = route.json()
    assert recommendation["routeId"] == "lingshan_easy"
    assert sum(recommendation["scoreBreakdown"].values()) == recommendation["score"]
    assert recommendation["spots"]


def test_unified_algorithm_safety_alert_is_leader_only_websocket_event(
    client, auth_helpers, fake_deepseek, monkeypatch
):
    import app.services.ai as ai_service

    async def fixed_asr(*args, **kwargs):
        return {
            "text": "我和团队走散了，现在找不到团长",
            "confidence": 0.99,
            "success": True,
            "format": "wav",
            "warning": None,
        }

    async def fixed_tts(*args, **kwargs):
        return {
            "audioUrl": "/uploads/tts/safety-test.mp3",
            "duration": 1.0,
            "success": True,
            "warning": None,
        }

    monkeypatch.setattr(ai_service, "asr_transcribe", fixed_asr)
    monkeypatch.setattr(ai_service, "tts_synthesize", fixed_tts)
    guide = auth_helpers["register"]("guide", "alert-guide")
    tourist = auth_helpers["register"]("tourist", "alert-tourist")
    headers = auth_helpers["headers"]
    room_id = auth_helpers["create_room"](guide)
    client.post(f"/api/rooms/{room_id}/join", headers=headers(tourist), json={})
    ticket = client.post(
        "/api/auth/ws-ticket", headers=headers(guide), json={"roomId": room_id}
    ).json()["ticket"]

    with client.websocket_connect(f"/ws/rooms/{room_id}?ticket={ticket}") as leader_socket:
        assert leader_socket.receive_json()["type"] == "room.connected"
        response = client.post(
            "/api/ai/public-voice-question",
            headers=headers(tourist),
            json={
                "roomId": room_id,
                "userId": tourist["userId"],
                "channel": "private",
                "audioUrl": "https://example.com/audio/lost.wav",
                "audioFormat": "wav",
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["decision"] == "emergency_alert"
        assert response.json()["provider"] == "deepseek"
        alert = leader_socket.receive_json()
        assert alert["type"] == "room.alert"
        assert alert["data"]["riskLevel"] == "high"
