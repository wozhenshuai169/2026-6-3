# A5 API Examples

Start the main backend first:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend clients should only call `/api/...`. Algorithm `/v1/...` endpoints are internal/debug only.

## Register

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"userName":"visitor01","password":"123456"}'
```

## Create Room

```bash
curl -X POST http://127.0.0.1:8000/api/rooms \
  -H "Content-Type: application/json" \
  -d '{"token":"<token>","roomName":"demo","scenicAreaId":"demo_scenic","routeId":"classic"}'
```

## Join Room

```bash
curl -X POST http://127.0.0.1:8000/api/rooms/<roomId>/join \
  -H "Content-Type: application/json" \
  -d '{"token":"<token>"}'
```

## Update Current Spot

```bash
curl -X POST http://127.0.0.1:8000/api/rooms/<roomId>/current-spot \
  -H "Content-Type: application/json" \
  -d '{"spotId":"main_hall"}'
```

## Public Text Question

```bash
curl -X POST http://127.0.0.1:8000/api/ai/public-question \
  -H "Content-Type: application/json" \
  -d '{
    "roomId":"<roomId>",
    "userId":"<userId>",
    "question":"这个建筑是什么时候建的？",
    "needAudio":true
  }'
```

Response shape:

```json
{
  "roomId": "room_001",
  "answer": "这座建筑始建于明代……",
  "audioUrl": "/uploads/tts/tts_room_001_1718092300_a8f3.mp3",
  "duration": 3.8,
  "sources": [{"title": "主展厅历史资料", "chunkId": "chunk_001"}],
  "avatarState": {
    "status": "speaking",
    "emotion": "friendly",
    "action": "answer",
    "mouthOpen": true
  },
  "warning": null
}
```

If TTS fails, `answer` is still returned:

```json
{
  "roomId": "room_001",
  "answer": "这座建筑始建于明代……",
  "audioUrl": null,
  "duration": 0,
  "sources": [],
  "avatarState": {
    "status": "idle",
    "emotion": "friendly",
    "action": "answer",
    "mouthOpen": false
  },
  "warning": "TTS failed, text answer returned only."
}
```

## Public Voice Question

```bash
curl -X POST http://127.0.0.1:8000/api/ai/public-voice-question \
  -H "Content-Type: application/json" \
  -d '{
    "roomId":"<roomId>",
    "userId":"<userId>",
    "channel":"public",
    "audioUrl":"https://example.com/question.wav",
    "audioFormat":"wav"
  }'
```

## TTS

```bash
curl -X POST http://127.0.0.1:8000/api/audio/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"欢迎来到主展厅。","voice":"guide_female","speed":1.0,"audioFormat":"mp3"}'
```

## Vision

```bash
curl -X POST http://127.0.0.1:8000/api/vision/recognize \
  -H "Content-Type: application/json" \
  -d '{"roomId":"<roomId>","userId":"<userId>","imageUrl":"https://example.com/spot.jpg","currentSpotId":"main_hall"}'
```

## Spots and Routes

```bash
curl http://127.0.0.1:8000/api/spots/main_hall
curl http://127.0.0.1:8000/api/spots/main_hall/nearby
curl http://127.0.0.1:8000/api/routes
curl http://127.0.0.1:8000/api/routes/classic
```

## Route Recommendation

```bash
curl -X POST http://127.0.0.1:8000/api/recommend/route \
  -H "Content-Type: application/json" \
  -d '{
    "roomId":"<roomId>",
    "userId":"<userId>",
    "preferences":{
      "interest":["history"],
      "timeLimit":60,
      "physicalStrength":"medium",
      "withChildren":false,
      "withElderly":true,
      "avoidCrowd":true
    }
  }'
```

## Knowledge Base

```bash
curl -X POST http://127.0.0.1:8000/api/kb/upload \
  -F "file=@./docs/demo.md"

curl http://127.0.0.1:8000/api/kb/docs

curl -X POST http://127.0.0.1:8000/api/kb/rebuild

curl -X POST http://127.0.0.1:8000/api/kb/test-query \
  -H "Content-Type: application/json" \
  -d '{"query":"主展厅 历史","limit":5}'
```

## Dashboard

```bash
curl http://127.0.0.1:8000/api/dashboard/overview
curl http://127.0.0.1:8000/api/dashboard/hot-questions
curl http://127.0.0.1:8000/api/dashboard/hot-spots
curl http://127.0.0.1:8000/api/dashboard/system-metrics
```
