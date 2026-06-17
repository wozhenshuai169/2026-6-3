from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _register(name: str = "tester") -> dict:
    response = client.post("/api/auth/register", json={"userName": name, "password": "123456"})
    assert response.status_code == 200, response.text
    return response.json()


def _create_room(route_id: str = "short") -> tuple[dict, dict]:
    user = _register("guide")
    response = client.post(
        "/api/rooms",
        json={
            "token": user["token"],
            "roomName": "demo room",
            "scenicAreaId": "area_001",
            "routeId": route_id,
        },
    )
    assert response.status_code == 200, response.text
    return user, response.json()


def test_audio_upload_multipart_asr_and_voice_logs():
    user, room = _create_room()

    upload = client.post(
        "/api/audio/upload",
        data={"roomId": room["roomId"], "userId": user["userId"], "channel": "public", "audioFormat": "webm"},
        files={"file": ("question.webm", b"demo audio", "audio/webm")},
    )
    assert upload.status_code == 200, upload.text
    assert upload.json()["audioUrl"].startswith("/uploads/audio/")

    asr = client.post(
        "/api/audio/asr",
        data={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "channel": "public",
            "audioFormat": "webm",
            "textHint": "where is the service center",
        },
        files={"file": ("question.webm", b"demo audio", "audio/webm")},
    )
    assert asr.status_code == 200, asr.text
    assert asr.json()["text"] == "where is the service center"

    voice = client.post(
        "/api/ai/public-voice-question",
        data={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "channel": "public",
            "audioFormat": "webm",
            "textHint": "tell me about this place",
        },
        files={"file": ("question.webm", b"demo audio", "audio/webm")},
    )
    assert voice.status_code == 200, voice.text
    assert voice.json()["asrText"] == "tell me about this place"

    logs = client.get(f"/api/rooms/{room['roomId']}/voice-logs")
    assert logs.status_code == 200, logs.text
    assert any(item.get("stage") == "voice_question" for item in logs.json()["items"])


def test_room_route_vision_recommendation_and_feedback_completion():
    user, room = _create_room("short")

    status = client.get(f"/api/rooms/{room['roomId']}")
    assert status.status_code == 200, status.text
    assert status.json()["routeId"] == "short"
    assert "routeSpotIds" in status.json()

    add_spot = client.post(
        f"/api/rooms/{room['roomId']}/add-spot",
        json={"spotId": "bell_tower", "position": "append", "source": "vision"},
    )
    assert add_spot.status_code == 200, add_spot.text
    route_spots = add_spot.json()["routeSpotIds"]
    assert route_spots.count("bell_tower") == 1

    vision = client.post(
        "/api/vision/recognize",
        json={"roomId": room["roomId"], "userId": user["userId"], "imageUrl": "bell_tower_photo.jpg"},
    )
    assert vision.status_code == 200, vision.text

    vision_logs = client.get(f"/api/rooms/{room['roomId']}/vision-logs")
    assert vision_logs.status_code == 200, vision_logs.text
    assert vision_logs.json()["items"][0]["recognizedSpot"]["spotId"]

    recommend = client.post(
        "/api/recommend/route",
        json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "preferences": {
                "interest": [],
                "timeLimit": 60,
                "physicalStrength": "low",
                "withChildren": False,
                "withElderly": True,
                "avoidCrowd": True,
            },
        },
    )
    assert recommend.status_code == 200, recommend.text
    payload = recommend.json()
    assert payload["suitableFor"]
    assert payload["notes"]

    recommendation_logs = client.get(f"/api/rooms/{room['roomId']}/recommendation-logs")
    assert recommendation_logs.status_code == 200, recommendation_logs.text
    assert recommendation_logs.json()["items"][0]["routeId"] == payload["routeId"]

    feedback = client.post(
        "/api/feedback",
        json={"roomId": room["roomId"], "userId": user["userId"], "scene": "panorama", "score": 5},
    )
    assert feedback.status_code == 200, feedback.text
    satisfaction = client.get("/api/dashboard/satisfaction")
    assert satisfaction.status_code == 200, satisfaction.text
    assert satisfaction.json()["averageScore"] >= 5
