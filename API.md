# A5 智能导游系统 — API 接口文档

## 基础信息

- 服务地址：`http://127.0.0.1:8000`
- 内容类型：`application/json`
- 所有接口均返回 JSON 格式

---

## 一、用户与房间管理

### 1. 用户注册

```
POST /api/auth/register
```

**请求体：**
```json
{
  "userName": "游客张三",
  "password": "123456"
}
```

**响应：**
```json
{
  "userId": "uuid",
  "userName": "游客张三",
  "token": "uuid"
}
```

> 注册成功后返回 `token`，后续房间操作需要携带。

---

### 2. 创建房间

```
POST /api/rooms
```

**请求体：**
```json
{
  "token": "用户token",
  "roomName": "故宫导览团",
  "scenicAreaId": "area_001",
  "routeId": "route_001"
}
```

**响应：**
```json
{
  "roomId": "uuid",
  "status": "created"
}
```

> 团长创建导览房间，返回 `roomId` 供其他游客加入。

---

### 3. 获取房间状态

```
GET /api/rooms/{roomId}
```

**响应：**
```json
{
  "roomId": "uuid",
  "members": [
    { "userId": "uuid", "userName": "张三" }
  ],
  "currentSpot": "spot_002",
  "status": "active"
}
```

---

### 4. 加入房间

```
POST /api/rooms/{roomId}/join
```

**请求体：**
```json
{
  "token": "用户token"
}
```

**响应：**
```json
{
  "roomId": "uuid",
  "userId": "uuid",
  "status": "joined"
}
```

---

### 5. 更新当前景点

```
POST /api/rooms/{roomId}/current-spot
```

**请求体：**
```json
{
  "spotId": "spot_003"
}
```

**响应：**
```json
{
  "roomId": "uuid",
  "currentSpot": "spot_003",
  "status": "updated"
}
```

> 当游客移动到新景点时调用，用于驱动 AI 决策和导览讲解。

---

### 6. 数字人状态

```
GET /api/rooms/{roomId}/avatar-state
```

**响应：**
```json
{
  "aiStatus": "speaking",
  "emotion": "friendly",
  "action": "speaking",
  "text": "欢迎来到主展厅！让我为您介绍这里的历史和文化。",
  "audioUrl": "/mock/audio/xxx.mp3"
}
```

**字段说明：**

| 字段 | 说明 | 可选值 |
|------|------|--------|
| `aiStatus` | AI 导游当前状态 | `idle`（待机）、`listening`（聆听）、`speaking`（说话）、`thinking`（思考）、`paused`（暂停）、`resuming`（续讲） |
| `emotion` | 表情 | `friendly`、`neutral`、`thinking`、`surprised` |
| `action` | 当前动作 | 同 `aiStatus` |
| `text` | 当前口播/字幕文本 | — |
| `audioUrl` | 对应 TTS 音频地址 | — |

> 前端数字人轮询此接口，根据返回的状态切换动画和播放语音。

---

## 二、AI 问答

### 7. 文本公共问答

```
POST /api/ai/public-question
```

**请求体：**
```json
{
  "roomId": "uuid",
  "userId": "user_001",
  "question": "这个建筑是什么时候建的？"
}
```

**响应：**
```json
{
  "roomId": "uuid",
  "answer": "关于「这个建筑是什么时候建的？」的解答：..."
}
```

> 文本输入 → 返回文本答案。适用于文字输入场景。

---

### 8. 语音公共问答（完整链路）

```
POST /api/ai/public-voice-question
```

**请求体：**
```json
{
  "roomId": "uuid",
  "userId": "user_001",
  "channel": "public",
  "audioUrl": "/uploads/audio/question.wav"
}
```

**响应：**
```json
{
  "asrText": "这个建筑是什么时候建的？",
  "decision": "interrupt_and_answer",
  "answer": "这个建筑始建于明代，清代曾进行过修缮。",
  "audioUrl": "/uploads/tts/answer_001.mp3",
  "resumeText": "刚才我们讲到它的历史沿革，接下来继续看屋顶装饰。",
  "resumeAudioUrl": "/uploads/tts/resume_001.mp3",
  "sources": [
    { "title": "主展厅历史资料", "chunkId": "chunk_001" }
  ]
}
```

**处理流程：**
```
录音上传 → ASR语音识别 → 介入决策 → RAG知识问答 → TTS语音合成 → 返回
                                                      ↓
                                               续讲文本生成 → TTS
```

**字段说明：**

| 字段 | 说明 |
|------|------|
| `asrText` | 语音识别后的文字 |
| `decision` | AI 决策类型（`interrupt_and_answer` / `public_reply` / `private_reply`） |
| `answer` | 知识问答生成的文本答案 |
| `audioUrl` | 答案的 TTS 语音文件地址 |
| `resumeText` | 回答完后继续导览的衔接文本 |
| `resumeAudioUrl` | 续讲文本的 TTS 语音地址 |
| `sources` | 答案引用的知识来源 |

> 一键完成"录音→问答→播报→续讲"全流程。前端只需上传录音文件，即可拿到文字答案和语音。

---

## 三、语音处理

### 9. 语音识别（ASR）

```
POST /api/audio/asr
```

**请求体：**
```json
{
  "roomId": "uuid",
  "userId": "user_001",
  "channel": "public",
  "audioUrl": "/uploads/audio/question.wav"
}
```

**响应：**
```json
{
  "text": "这个建筑是什么时候建的？",
  "confidence": 0.92
}
```

| 字段 | 说明 |
|------|------|
| `text` | 识别出的文本内容 |
| `confidence` | 置信度（0~1） |
| `channel` | 频道类型：`public`（公共频道）或 `private`（私人频道） |

> 将语音文件转写为文字。可作为独立接口使用，也可嵌入语音问答链路。

---

### 10. 语音合成（TTS）

```
POST /api/audio/tts
```

**请求体：**
```json
{
  "text": "这个建筑始建于明代，清代曾进行过修缮。",
  "voice": "guide_female",
  "speed": 1.0
}
```

**响应：**
```json
{
  "audioUrl": "/uploads/tts/answer_001.mp3",
  "duration": 8.5
}
```

| 字段 | 说明 |
|------|------|
| `text` | 需要合成语音的文本 |
| `voice` | 音色选择（如 `guide_female`） |
| `speed` | 语速倍率（默认 1.0） |
| `audioUrl` | 合成后的语音文件地址 |
| `duration` | 音频时长（秒） |

> 将文本转为语音文件。可用于答案播报、续讲提示等场景。

---

## 四、图片识景

### 11. 图片识景

```
POST /api/vision/recognize
```

**请求体：**
```json
{
  "roomId": "uuid",
  "userId": "user_001",
  "imageUrl": "/uploads/images/photo.jpg",
  "currentSpotId": "spot_001"
}
```

**响应：**
```json
{
  "recognizedSpot": {
    "spotId": "spot_003",
    "spotName": "钟楼",
    "confidence": 0.87
  },
  "description": "你拍到的是钟楼，它是景区内保存较完整的传统建筑之一……",
  "relatedSpots": [
    { "spotId": "spot_004", "spotName": "鼓楼" }
  ]
}
```

| 字段 | 说明 |
|------|------|
| `imageUrl` | 游客拍摄的图片地址 |
| `currentSpotId` | 当前所在景点（辅助识别，可选） |
| `recognizedSpot` | 识别到的景点信息（含置信度） |
| `description` | 对该景点的文字介绍 |
| `relatedSpots` | 推荐的相关景点 |

> 游客拍照后调用，AI 识别图片中的景点并返回介绍和周边推荐。

---

## 五、路线推荐

### 12. 路线推荐

```
POST /api/recommend/route
```

**请求体：**
```json
{
  "roomId": "uuid",
  "userId": "user_002",
  "preferences": {
    "interest": ["历史", "摄影"],
    "timeLimit": 60,
    "physicalStrength": "medium",
    "withChildren": false,
    "withElderly": true,
    "avoidCrowd": true
  }
}
```

**响应：**
```json
{
  "routeName": "历史轻松线",
  "estimatedTime": 55,
  "spots": [
    { "spotId": "spot_001", "spotName": "入口广场", "stayMinutes": 5 },
    { "spotId": "spot_002", "spotName": "主展厅", "stayMinutes": 20 },
    { "spotId": "spot_005", "spotName": "休息区", "stayMinutes": 10 }
  ],
  "reason": "该路线步行距离较短，包含休息点，适合有老人同行的游客。"
}
```

**偏好参数说明：**

| 参数 | 说明 | 可选值 |
|------|------|--------|
| `interest` | 兴趣标签 | `"历史"` `"摄影"` 等 |
| `timeLimit` | 时间限制（分钟） | 整数 |
| `physicalStrength` | 体力水平 | `"low"` `"medium"` `"high"` |
| `withChildren` | 是否带孩子 | `true` / `false` |
| `withElderly` | 是否有老人 | `true` / `false` |
| `avoidCrowd` | 是否避开拥挤 | `true` / `false` |

> 根据游客偏好自动推荐最优游览路线，包含各景点停留时长和推荐理由。

---

## 接口汇总

| # | 方法 | 路径 | 说明 |
|---|------|------|------|
| 1 | POST | `/api/auth/register` | 用户注册 |
| 2 | POST | `/api/rooms` | 创建房间 |
| 3 | GET | `/api/rooms/{roomId}` | 获取房间状态 |
| 4 | POST | `/api/rooms/{roomId}/join` | 加入房间 |
| 5 | POST | `/api/rooms/{roomId}/current-spot` | 更新当前景点 |
| 6 | GET | `/api/rooms/{roomId}/avatar-state` | 数字人状态 ⭐ |
| 7 | POST | `/api/ai/public-question` | 文本问答 |
| 8 | POST | `/api/ai/public-voice-question` | 语音问答链路 ⭐ |
| 9 | POST | `/api/audio/asr` | 语音识别 ⭐ |
| 10 | POST | `/api/audio/tts` | 语音合成 ⭐ |
| 11 | POST | `/api/vision/recognize` | 图片识景 ⭐ |
| 12 | POST | `/api/recommend/route` | 路线推荐 ⭐ |

> ⭐ 为本次新增接口（共 6 个）

---

## 错误处理

所有接口在房间不存在时返回：

```json
{ "detail": "房间不存在" }
```

HTTP 状态码：`404 Not Found`

请求参数校验失败时返回 `422 Unprocessable Entity`，由 Pydantic 自动校验。
