# A5 智能导游系统 — 接口样例

## 1. 用户注册

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"userName": "游客张三", "password": "123456"}'
```

```json
{
  "userId": "7c806fd3-51e3-41ea-8191-35882da887a9",
  "userName": "游客张三",
  "token": "837bf071-075a-4df3-9bb1-1716b7cbd81f"
}
```

## 2. 创建房间

```bash
curl -X POST http://127.0.0.1:8000/api/rooms \
  -H "Content-Type: application/json" \
  -d '{
    "token": "<注册返回的token>",
    "roomName": "故宫导览团",
    "scenicAreaId": "area_001",
    "routeId": "route_001"
  }'
```

```json
{
  "roomId": "9e147bf2-81f0-41e4-940f-11a76c9fb405",
  "status": "created"
}
```

## 3. 文本问答

```bash
curl -X POST http://127.0.0.1:8000/api/ai/public-question \
  -H "Content-Type: application/json" \
  -d '{
    "roomId": "<房间ID>",
    "userId": "<用户ID>",
    "question": "这个建筑是什么时候建的？"
  }'
```

```json
{
  "roomId": "9e147bf2-...",
  "answer": "这座建筑始建于明代永乐年间（约1406年），..."
}
```

## 4. 图片识景

```bash
curl -X POST http://127.0.0.1:8000/api/vision/recognize \
  -H "Content-Type: application/json" \
  -d '{
    "roomId": "<房间ID>",
    "userId": "<用户ID>",
    "imageUrl": "http://127.0.0.1:8000/uploads/1.jpg",
    "currentSpotId": "spot_001"
  }'
```

```json
{
  "recognizedSpot": {
    "spotId": "bell_tower",
    "spotName": "钟楼",
    "confidence": 0.92
  },
  "description": "你拍到的是钟楼，这是景区内保存较完整的传统建筑之一……",
  "relatedSpots": [
    { "spotId": "drum_tower", "spotName": "鼓楼" }
  ],
  "visualFeatures": ["木结构", "重檐", "红墙"],
  "category": "spot"
}
```

## 5. 语音合成 (TTS)

```bash
curl -X POST http://127.0.0.1:8000/api/audio/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "欢迎来到故宫博物院！",
    "voice": "guide_female",
    "speed": 1.0,
    "audioFormat": "mp3"
  }'
```

```json
{
  "audioUrl": "/uploads/tts/e6710f49fcdf.mp3",
  "duration": 1.9
}
```

> 音频可直接访问: `http://127.0.0.1:8000/uploads/tts/e6710f49fcdf.mp3`

## 6. 语音识别 (ASR)

```bash
curl -X POST http://127.0.0.1:8000/api/audio/asr \
  -H "Content-Type: application/json" \
  -d '{
    "roomId": "<房间ID>",
    "userId": "<用户ID>",
    "channel": "public",
    "audioUrl": "https://example.com/audio/question.wav",
    "audioFormat": "wav",
    "textHint": ""
  }'
```

```json
{
  "text": "这个建筑是什么时候建的？",
  "confidence": 0.95
}
```

> **注意**: ASR 需要音频文件有公网可访问的 URL（如 OSS 链接）。

## 7. 语音问答完整链路

```bash
curl -X POST http://127.0.0.1:8000/api/ai/public-voice-question \
  -H "Content-Type: application/json" \
  -d '{
    "roomId": "<房间ID>",
    "userId": "<用户ID>",
    "channel": "public",
    "audioUrl": "https://oss.example.com/audio/question.wav"
  }'
```

```json
{
  "asrText": "这个建筑是什么时候建的？",
  "decision": "interrupt_and_answer",
  "answer": "这座建筑始建于明代……",
  "audioUrl": "/uploads/tts/answer_001.mp3",
  "resumeText": "刚才我们讲到它的历史沿革，接下来继续看屋顶装饰。",
  "resumeAudioUrl": "/uploads/tts/resume_001.mp3",
  "sources": [
    { "title": "主展厅历史资料", "chunkId": "chunk_001" }
  ]
}
```

## 8. 路线推荐

```bash
curl -X POST http://127.0.0.1:8000/api/recommend/route \
  -H "Content-Type: application/json" \
  -d '{
    "roomId": "<房间ID>",
    "userId": "<用户ID>",
    "preferences": {
      "interest": ["历史", "摄影"],
      "timeLimit": 60,
      "physicalStrength": "medium",
      "withChildren": false,
      "withElderly": true,
      "avoidCrowd": true
    }
  }'
```

## 音色列表 (TTS)

| voice | 对应引擎 | 风格 |
|-------|---------|------|
| `guide_female` | zh-CN-XiaoxiaoNeural | 温柔女声（默认）|
| `guide_male` | zh-CN-YunxiNeural | 成熟男声 |
| `xiaomei` | zh-CN-XiaoyiNeural | 活泼女声 |
| `xiaowei` | zh-CN-YunyangNeural | 新闻男声 |
