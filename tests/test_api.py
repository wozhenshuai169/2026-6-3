"""
功能测试：覆盖 FastAPI 应用层所有 API 端点。

运行方式（在项目根目录 d:\\软件杯）：
    pytest tests/test_api.py -v
    或
    python -m pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── 工具函数 ──────────────────────────────────────────────

def register_user(name: str = "测试游客") -> dict:
    """注册一个新用户并返回完整的 response JSON。"""
    resp = client.post("/api/auth/register", json={
        "userName": name,
        "password": "123456",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


def create_room(token: str, room_name: str = "测试房间",
                scenic_id: str = "scenic_001", route_id: str = "route_001") -> dict:
    """创建一个新房间并返回完整的 response JSON。"""
    resp = client.post("/api/rooms", json={
        "token": token,
        "roomName": room_name,
        "scenicAreaId": scenic_id,
        "routeId": route_id,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


# ═══════════════════════════════════════════════════════════
# 健康检查
# ═══════════════════════════════════════════════════════════

class TestHealthCheck:
    """GET / — 根路径健康检查"""

    def test_root_returns_message(self):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "A5 Backend Running"


# ═══════════════════════════════════════════════════════════
# 用户认证  /api/auth
# ═══════════════════════════════════════════════════════════

class TestAuthRegister:
    """POST /api/auth/register — 用户注册"""

    def test_register_returns_200_with_correct_fields(self):
        resp = client.post("/api/auth/register", json={
            "userName": "张三",
            "password": "pass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "userId" in data
        assert data["userName"] == "张三"
        assert "token" in data
        assert len(data["token"]) > 0

    def test_register_multiple_users_get_unique_ids(self):
        u1 = register_user("用户A")
        u2 = register_user("用户B")
        assert u1["userId"] != u2["userId"]
        assert u1["token"] != u2["token"]

    def test_register_missing_fields_returns_422(self):
        resp = client.post("/api/auth/register", json={})
        assert resp.status_code == 422

    def test_register_missing_password_returns_422(self):
        resp = client.post("/api/auth/register", json={"userName": "test"})
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════
# 房间管理  /api/rooms
# ═══════════════════════════════════════════════════════════

class TestRoomCreate:
    """POST /api/rooms — 创建房间"""

    def test_create_room_with_valid_token(self):
        user = register_user("房主")
        resp = client.post("/api/rooms", json={
            "token": user["token"],
            "roomName": "故宫深度游",
            "scenicAreaId": "scenic_001",
            "routeId": "route_001",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "roomId" in data
        assert data["status"] == "created"

    def test_create_room_with_invalid_token_returns_401(self):
        resp = client.post("/api/rooms", json={
            "token": "invalid-token-xxxxx",
            "roomName": "test",
            "scenicAreaId": "s1",
            "routeId": "r1",
        })
        assert resp.status_code == 401
        assert resp.json()["detail"] == "无效的认证令牌"

    def test_create_room_missing_token_returns_422(self):
        resp = client.post("/api/rooms", json={
            "roomName": "test",
            "scenicAreaId": "s1",
            "routeId": "r1",
        })
        assert resp.status_code == 422


class TestRoomGetStatus:
    """GET /api/rooms/{roomId} — 获取房间状态"""

    def test_get_existing_room(self):
        user = register_user("查询者")
        room = create_room(user["token"], "我的房间")
        resp = client.get(f"/api/rooms/{room['roomId']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["roomId"] == room["roomId"]
        assert data["status"] == "active"
        assert isinstance(data["members"], list)
        assert "currentSpot" in data

    def test_get_nonexistent_room_returns_404(self):
        resp = client.get("/api/rooms/nonexistent-room-id")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "房间不存在"


class TestRoomJoin:
    """POST /api/rooms/{roomId}/join — 加入房间"""

    def test_join_room_with_valid_token(self):
        owner = register_user("房主A")
        room = create_room(owner["token"], "可加入房")
        joiner = register_user("加入者A")

        resp = client.post(f"/api/rooms/{room['roomId']}/join", json={
            "token": joiner["token"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["roomId"] == room["roomId"]
        assert data["userId"] == joiner["userId"]
        assert data["status"] == "joined"

    def test_join_nonexistent_room_returns_404(self):
        user = register_user("幽灵加入者")
        resp = client.post("/api/rooms/ghost-room-id/join", json={
            "token": user["token"],
        })
        assert resp.status_code == 404
        assert resp.json()["detail"] == "房间不存在"

    def test_join_room_with_invalid_token_returns_401(self):
        owner = register_user("房主B")
        room = create_room(owner["token"], "私密房")
        resp = client.post(f"/api/rooms/{room['roomId']}/join", json={
            "token": "bad-token",
        })
        assert resp.status_code == 401
        assert resp.json()["detail"] == "无效的认证令牌"

    def test_join_room_members_list_grows(self):
        """验证加入后房间成员列表确实增长"""
        owner = register_user("房主C")
        room = create_room(owner["token"], "测试增长")

        # 初始成员列表为空（leader 不在 members 里）
        status_before = client.get(f"/api/rooms/{room['roomId']}").json()
        count_before = len(status_before["members"])

        joiner = register_user("加入者C")
        client.post(f"/api/rooms/{room['roomId']}/join", json={
            "token": joiner["token"],
        })

        status_after = client.get(f"/api/rooms/{room['roomId']}").json()
        assert len(status_after["members"]) == count_before + 1
        assert status_after["members"][-1]["userId"] == joiner["userId"]


class TestRoomUpdateSpot:
    """POST /api/rooms/{roomId}/current-spot — 更新当前景点"""

    def test_update_spot_success(self):
        user = register_user("导游A")
        room = create_room(user["token"], "景点更新房")
        resp = client.post(f"/api/rooms/{room['roomId']}/current-spot", json={
            "spotId": "spot_002",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["roomId"] == room["roomId"]
        assert data["currentSpot"] == "spot_002"
        assert data["status"] == "updated"

    def test_update_spot_nonexistent_room_returns_404(self):
        resp = client.post("/api/rooms/fake-room/current-spot", json={
            "spotId": "spot_001",
        })
        assert resp.status_code == 404

    def test_update_spot_persists(self):
        """验证更新后 GET 能看到新景点"""
        user = register_user("导游B")
        room = create_room(user["token"], "持久化房")
        client.post(f"/api/rooms/{room['roomId']}/current-spot", json={
            "spotId": "spot_003",
        })
        status = client.get(f"/api/rooms/{room['roomId']}").json()
        assert status["currentSpot"] == "spot_003"


class TestAvatarState:
    """GET /api/rooms/{roomId}/avatar-state — 数字人状态"""

    def test_avatar_state_for_existing_room(self):
        user = register_user("数字人测试")
        room = create_room(user["token"], "验证房")
        resp = client.get(f"/api/rooms/{room['roomId']}/avatar-state")
        assert resp.status_code == 200
        data = resp.json()
        assert "aiStatus" in data
        assert "emotion" in data
        assert "action" in data
        assert "text" in data
        assert "audioUrl" in data
        # 房间刚创建，有 leader 但无 members → member_count == 0
        assert data["aiStatus"] == "idle"

    def test_avatar_state_nonexistent_room_returns_404(self):
        resp = client.get("/api/rooms/ghost-room/avatar-state")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "房间不存在"

    def test_avatar_state_with_spot_returns_speaking(self):
        """设置景点 + 有成员 → aiStatus 应为 speaking"""
        owner = register_user("导游X")
        room = create_room(owner["token"], "讲解房")
        # 有人加入 → member_count > 0
        joiner = register_user("游客X")
        client.post(f"/api/rooms/{room['roomId']}/join", json={
            "token": joiner["token"],
        })
        # 设置景点
        client.post(f"/api/rooms/{room['roomId']}/current-spot", json={
            "spotId": "spot_001",
        })

        resp = client.get(f"/api/rooms/{room['roomId']}/avatar-state")
        assert resp.status_code == 200
        data = resp.json()
        assert data["aiStatus"] == "speaking"
        assert data["emotion"] == "friendly"
        assert data["action"] == "speaking"
        assert "spot_001" in data["text"] or "入口广场" in data["text"]


# ═══════════════════════════════════════════════════════════
# 音频处理  /api/audio
# ═══════════════════════════════════════════════════════════

class TestAudioASR:
    """POST /api/audio/asr — 语音识别"""

    def test_asr_existing_room(self):
        """带 text_hint → 高置信度直接返回"""
        user = register_user("ASR测试者")
        room = create_room(user["token"])
        client.post(f"/api/rooms/{room['roomId']}/current-spot", json={
            "spotId": "spot_002",
        })
        resp = client.post("/api/audio/asr", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "channel": "public",
            "audioUrl": "https://example.com/audio/test.wav",
            "textHint": "请问这个建筑有什么历史？",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "text" in data
        assert "confidence" in data
        assert data["confidence"] == 0.88  # text_hint 高置信度
        assert "这个建筑有什么历史" in data["text"]

    def test_asr_nonexistent_room_returns_404(self):
        resp = client.post("/api/audio/asr", json={
            "roomId": "fake-room-id",
            "userId": "user_001",
            "channel": "public",
            "audioUrl": "https://example.com/audio/test.wav",
        })
        assert resp.status_code == 404
        assert resp.json()["detail"] == "房间不存在"

    def test_asr_without_spot_returns_generic_text(self):
        """无 demo 关键词 → 低置信度通用文本"""
        user = register_user("ASR无景点")
        room = create_room(user["token"])
        resp = client.post("/api/audio/asr", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "channel": "public",
            "audioUrl": "https://example.com/test.wav",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["confidence"] == 0.35  # 无关键词匹配，低置信度
        assert "景区" in data["text"]

    def test_asr_private_channel(self):
        """私人频道 ASR 也正常工作"""
        user = register_user("ASR私聊")
        room = create_room(user["token"])
        resp = client.post("/api/audio/asr", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "channel": "private",
            "audioUrl": "https://example.com/private.wav",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["confidence"] == 0.35  # 无关键词匹配


class TestAudioTTS:
    """POST /api/audio/tts — 语音合成"""

    def test_tts_default_params(self):
        resp = client.post("/api/audio/tts", json={
            "text": "欢迎来到故宫博物院，这里是中国最大的古代文化艺术博物馆。",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "audioUrl" in data
        assert "duration" in data
        assert data["audioUrl"].startswith("/static/tts/")  # 对齐 VoiceAdapter.tts()
        assert data["duration"] > 0

    def test_tts_custom_voice_and_speed(self):
        resp = client.post("/api/audio/tts", json={
            "text": "前方是钟楼，建于明代。",
            "voice": "guide_male",
            "speed": 1.5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["duration"], (int, float))
        # 速度加倍，duration 应该减少
        assert data["duration"] > 0

    def test_tts_short_text_min_duration(self):
        """短文本最小 900ms → 0.9s"""
        resp = client.post("/api/audio/tts", json={
            "text": "你好",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["duration"] >= 0.9  # 对齐 VoiceAdapter: min 900ms

    def test_tts_same_text_same_url(self):
        """相同文本应生成相同音频 URL"""
        text = "前方转弯"
        resp1 = client.post("/api/audio/tts", json={"text": text})
        resp2 = client.post("/api/audio/tts", json={"text": text})
        assert resp1.json()["audioUrl"] == resp2.json()["audioUrl"]

    def test_tts_empty_body_returns_422(self):
        resp = client.post("/api/audio/tts", json={})
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════
# AI 问答  /api/ai
# ═══════════════════════════════════════════════════════════

class TestAIPublicQuestion:
    """POST /api/ai/public-question — 公共问答"""

    def test_public_question_existing_room(self):
        user = register_user("问答测试者")
        room = create_room(user["token"])
        resp = client.post("/api/ai/public-question", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "question": "这个建筑是什么时候建的？",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["roomId"] == room["roomId"]
        assert "answer" in data
        assert len(data["answer"]) > 0  # 真实 LLM / Mock 均有回答

    def test_public_question_nonexistent_room_returns_404(self):
        resp = client.post("/api/ai/public-question", json={
            "roomId": "fake-room",
            "userId": "user_001",
            "question": "这是哪里？",
        })
        assert resp.status_code == 404

    def test_public_question_with_current_spot(self):
        """有当前景点时，LLM 生成对应讲解"""
        user = register_user("景点问答")
        room = create_room(user["token"])
        client.post(f"/api/rooms/{room['roomId']}/current-spot", json={
            "spotId": "spot_002",
        })
        resp = client.post("/api/ai/public-question", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "question": "这里有什么历史？",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["answer"]) > 0  # 真实 LLM 回答


class TestAIVoiceQuestion:
    """POST /api/ai/public-voice-question — 语音问答完整链路"""

    def test_voice_question_public_channel(self):
        user = register_user("语音问答者")
        room = create_room(user["token"])
        client.post(f"/api/rooms/{room['roomId']}/current-spot", json={
            "spotId": "spot_001",
        })
        resp = client.post("/api/ai/public-voice-question", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "channel": "public",
            "audioUrl": "https://example.com/query.wav",
            "textHint": "这个建筑是什么时候建的？",  # text_hint 避免低置信度 → ask_clarification
        })
        assert resp.status_code == 200
        data = resp.json()
        # 检查完整链路的五个输出
        assert "asrText" in data
        assert data["decision"] == "interrupt_and_answer"  # text_hint → 高置信度 → 正常回答
        assert "answer" in data
        assert "audioUrl" in data
        assert data["audioUrl"].startswith("/static/tts/")  # 对齐 VoiceAdapter.tts()
        assert "resumeText" in data
        assert "resumeAudioUrl" in data
        # sources 包含至少一个来源
        assert len(data["sources"]) >= 1
        assert data["sources"][0]["title"] == "主展厅历史资料"

    def test_voice_question_private_channel(self):
        """私人频道 → decision 应为 private_reply"""
        user = register_user("私聊语音")
        room = create_room(user["token"])
        resp = client.post("/api/ai/public-voice-question", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "channel": "private",
            "audioUrl": "https://example.com/private-query.wav",
            "textHint": "附近有洗手间吗？",  # text_hint 避免低置信度 → ask_clarification
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "private_reply"

    def test_voice_question_nonexistent_room_returns_404(self):
        resp = client.post("/api/ai/public-voice-question", json={
            "roomId": "no-such-room",
            "userId": "user_001",
            "channel": "public",
            "audioUrl": "https://example.com/test.wav",
        })
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════
# 图片识景  /api/vision
# ═══════════════════════════════════════════════════════════

class TestVisionRecognize:
    """POST /api/vision/recognize — 图片识景"""

    def test_recognize_with_known_spot(self):
        """通过 imageUrl 中的关键词匹配 bell_tower"""
        user = register_user("识景者")
        room = create_room(user["token"])
        resp = client.post("/api/vision/recognize", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "imageUrl": "https://example.com/bell_tower_photo.jpg",  # 匹配 vision_spots.json
            "currentSpotId": "",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["recognizedSpot"]["spotId"] == "bell_tower"  # 对齐 vision_spots.json
        assert data["recognizedSpot"]["spotName"] == "钟楼"
        assert data["recognizedSpot"]["confidence"] == 0.87
        assert len(data["description"]) > 0
        assert len(data["relatedSpots"]) >= 1
        # 对齐新 VisionResult: 应有 visualFeatures
        assert len(data.get("visualFeatures", [])) >= 1

    def test_recognize_default_when_spot_unknown(self):
        """未知景点默认返回钟楼（回退）"""
        user = register_user("未知识景")
        room = create_room(user["token"])
        resp = client.post("/api/vision/recognize", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "imageUrl": "https://example.com/unknown_xyz.jpg",
            "currentSpotId": "",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["recognizedSpot"]["spotName"] == "钟楼"  # 默认回退到钟楼
        assert data["recognizedSpot"]["confidence"] == 0.28  # 未匹配，低置信度

    def test_recognize_uses_room_current_spot_when_not_given(self):
        """不传 currentSpotId 时使用房间的 currentSpot 作为 hint"""
        user = register_user("房间识景")
        room = create_room(user["token"])
        client.post(f"/api/rooms/{room['roomId']}/current-spot", json={
            "spotId": "main_hall",  # 使用 vision_spots.json 中的 spotId
        })
        resp = client.post("/api/vision/recognize", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "imageUrl": "https://example.com/main_hall.jpg",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["recognizedSpot"]["spotName"] == "主展厅"  # main_hall → 主展厅

    def test_recognize_nonexistent_room_returns_404(self):
        resp = client.post("/api/vision/recognize", json={
            "roomId": "ghost-room",
            "userId": "user_001",
            "imageUrl": "https://example.com/img.jpg",
        })
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════
# 路线推荐  /api/recommend
# ═══════════════════════════════════════════════════════════

class TestRouteRecommend:
    """POST /api/recommend/route — 路线推荐"""

    def test_recommend_default_route(self):
        """默认偏好 → routes.json 中得分最高的路线"""
        user = register_user("路线推荐者")
        room = create_room(user["token"])
        resp = client.post("/api/recommend/route", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "preferences": {
                "interest": [],
                "timeLimit": 60,
                "physicalStrength": "medium",
                "withChildren": False,
                "withElderly": False,
                "avoidCrowd": False,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        # 对齐 routes.json 加分制：所有路线都满足时间要求，得分最高者胜出
        assert "routeName" in data
        assert data["estimatedTime"] > 0
        assert len(data["spots"]) >= 1
        assert len(data["reason"]) > 0
        # 对齐新字段
        assert "scoreBreakdown" in data
        assert "difficulty" in data
        assert "matchedPreferences" in data

    def test_recommend_elderly_route(self):
        """有老人 → 优先低难度路线（加分制 staminaScore + companionScore）"""
        user = register_user("老人路线")
        room = create_room(user["token"])
        resp = client.post("/api/recommend/route", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "preferences": {
                "interest": [],
                "timeLimit": 60,
                "physicalStrength": "medium",
                "withChildren": False,
                "withElderly": True,
                "avoidCrowd": False,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        # 对齐 routes.json 加分制：family_friendly + less_walking 路线得分更高
        assert data["difficulty"] in ("low", "medium")
        assert "less_walking" in data["matchedPreferences"] or "family_friendly" in data["matchedPreferences"]

    def test_recommend_history_interest_route(self):
        """兴趣包含"历史" → interestScore +3 的路线获胜"""
        user = register_user("历史迷")
        room = create_room(user["token"])
        resp = client.post("/api/recommend/route", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "preferences": {
                "interest": ["历史"],
                "timeLimit": 90,
                "physicalStrength": "high",
                "withChildren": False,
                "withElderly": False,
                "avoidCrowd": False,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        # 对齐加分制：interest=["历史"] 的路由有 interestScore=+3 优势
        assert data["scoreBreakdown"]["interestScore"] >= 3

    def test_recommend_children_route(self):
        """带小孩 → family_friendly 路线得分更高（companionScore +2）"""
        user = register_user("亲子游")
        room = create_room(user["token"])
        resp = client.post("/api/recommend/route", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "preferences": {
                "interest": [],
                "timeLimit": 60,
                "physicalStrength": "medium",
                "withChildren": True,
                "withElderly": False,
                "avoidCrowd": False,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "family_friendly" in data["matchedPreferences"]

    def test_recommend_low_strength_route(self):
        """体力低 → less_walking 路线有 staminaScore +2 优势"""
        user = register_user("体力低")
        room = create_room(user["token"])
        resp = client.post("/api/recommend/route", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "preferences": {
                "interest": [],
                "timeLimit": 60,
                "physicalStrength": "low",
                "withChildren": False,
                "withElderly": False,
                "avoidCrowd": False,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "less_walking" in data["matchedPreferences"]

    def test_recommend_avoid_crowd_route(self):
        """避拥挤 → avoidCrowd 触发 less_walking 偏好"""
        user = register_user("避人群")
        room = create_room(user["token"])
        resp = client.post("/api/recommend/route", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "preferences": {
                "interest": [],
                "timeLimit": 60,
                "physicalStrength": "medium",
                "withChildren": False,
                "withElderly": False,
                "avoidCrowd": True,
            },
        })
        assert resp.status_code == 200
        # 对齐：avoidCrowd 表示偏好轻松路线
        assert "reason" in resp.json()

    def test_recommend_nonexistent_room_returns_404(self):
        resp = client.post("/api/recommend/route", json={
            "roomId": "fake-room",
            "userId": "user_001",
            "preferences": {
                "interest": [],
                "timeLimit": 60,
                "physicalStrength": "medium",
                "withChildren": False,
                "withElderly": False,
                "avoidCrowd": True,
            },
        })
        assert resp.status_code == 404

    def test_recommend_all_spots_have_required_fields(self):
        """每个推荐景点都包含 spotId, spotName, stayMinutes"""
        user = register_user("字段验证")
        room = create_room(user["token"])
        resp = client.post("/api/recommend/route", json={
            "roomId": room["roomId"],
            "userId": user["userId"],
            "preferences": {
                "interest": [],
                "timeLimit": 60,
                "physicalStrength": "medium",
                "withChildren": False,
                "withElderly": False,
                "avoidCrowd": False,
            },
        })
        for spot in resp.json()["spots"]:
            assert "spotId" in spot
            assert "spotName" in spot
            assert "stayMinutes" in spot
            assert isinstance(spot["stayMinutes"], int)
            assert spot["stayMinutes"] > 0


# ═══════════════════════════════════════════════════════════
# 422 验证错误
# ═══════════════════════════════════════════════════════════

class TestValidationErrors:
    """Pydantic 验证 → 422"""

    @pytest.mark.parametrize("endpoint,body", [
        ("/api/rooms", {}),
        ("/api/rooms", {"token": "t"}),
        ("/api/rooms/nonexistent/join", {}),
        ("/api/rooms/nonexistent/current-spot", {}),
        ("/api/audio/asr", {}),
        ("/api/ai/public-question", {}),
        ("/api/ai/public-voice-question", {}),
        ("/api/vision/recognize", {}),
        ("/api/recommend/route", {}),
    ])
    def test_missing_required_fields_returns_422(self, endpoint, body):
        resp = client.post(endpoint, json=body)
        assert resp.status_code == 422, f"{endpoint} with {body}: expected 422, got {resp.status_code}"


# ═══════════════════════════════════════════════════════════
# 端到端场景测试
# ═══════════════════════════════════════════════════════════

class TestEndToEndScenarios:
    """模拟完整的用户使用流程"""

    def test_full_guided_tour_flow(self):
        """完整导览流程：注册 → 创建房间 → 加入 → 设置景点 → ASR → 问答 → 路线推荐 → 化身状态"""
        # 1. 导游注册并创建房间
        guide = register_user("导游小王")
        room = create_room(guide["token"], "故宫一日游")

        # 2. 两名游客加入
        tourist_a = register_user("游客A")
        tourist_b = register_user("游客B")
        client.post(f"/api/rooms/{room['roomId']}/join", json={"token": tourist_a["token"]})
        client.post(f"/api/rooms/{room['roomId']}/join", json={"token": tourist_b["token"]})

        # 3. 验证房间成员
        status = client.get(f"/api/rooms/{room['roomId']}").json()
        assert len(status["members"]) == 2

        # 4. 导游设置当前景点
        client.post(f"/api/rooms/{room['roomId']}/current-spot", json={
            "spotId": "spot_002",
        })
        assert client.get(f"/api/rooms/{room['roomId']}").json()["currentSpot"] == "spot_002"

        # 5. 数字人状态应为 speaking
        avatar = client.get(f"/api/rooms/{room['roomId']}/avatar-state").json()
        assert avatar["aiStatus"] == "speaking"

        # 6. 游客语音提问（带 textHint 保证高置信度）
        voice_resp = client.post("/api/ai/public-voice-question", json={
            "roomId": room["roomId"],
            "userId": tourist_a["userId"],
            "channel": "public",
            "audioUrl": "https://example.com/question.wav",
            "textHint": "这个建筑有什么历史故事？",
        })
        assert voice_resp.status_code == 200
        assert voice_resp.json()["decision"] == "interrupt_and_answer"  # text_hint → 高置信度

        # 7. 路线推荐（兴趣为历史 → interestScore 加分）
        route_resp = client.post("/api/recommend/route", json={
            "roomId": room["roomId"],
            "userId": tourist_a["userId"],
            "preferences": {
                "interest": ["历史"],
                "timeLimit": 120,
                "physicalStrength": "medium",
                "withChildren": False,
                "withElderly": False,
                "avoidCrowd": False,
            },
        })
        assert route_resp.status_code == 200
        assert route_resp.json()["scoreBreakdown"]["interestScore"] >= 3

    def test_register_then_join_multiple_rooms(self):
        """用户加入多个房间"""
        user = register_user("多房用户")
        guide = register_user("多房导游")

        room1 = create_room(guide["token"], "上午场")
        room2 = create_room(guide["token"], "下午场")

        r1 = client.post(f"/api/rooms/{room1['roomId']}/join", json={"token": user["token"]})
        r2 = client.post(f"/api/rooms/{room2['roomId']}/join", json={"token": user["token"]})
        assert r1.status_code == 200
        assert r2.status_code == 200

        # 两个房间成员列表都应有该用户
        s1 = client.get(f"/api/rooms/{room1['roomId']}").json()
        s2 = client.get(f"/api/rooms/{room2['roomId']}").json()
        assert any(m["userId"] == user["userId"] for m in s1["members"])
        assert any(m["userId"] == user["userId"] for m in s2["members"])
