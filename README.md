# A5 智能导游系统

## 主后端启动方式

前端只访问主后端 `/api/...`，不要直接访问算法服务。

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

常用地址：

- API 服务：`http://127.0.0.1:8000`
- Swagger 文档：`http://127.0.0.1:8000/docs`
- OpenAPI：`http://127.0.0.1:8000/openapi.json`
- 静态文件：`http://127.0.0.1:8000/uploads/`

## 联调架构

```text
frontend-v2
  -> /api/...
app.main
  -> app/services + providers
  -> algorithm_service or model providers
LLM / RAG / ASR / TTS / Vision / Route
```

前端唯一入口：`/api/...`

算法服务内部调试入口：`/v1/...`

`/v1` 只保留给主后端内部调用或算法同学本地调试，不作为前端联调路径。

## 主后端接口

- `POST /api/auth/register`
- `POST /api/rooms`
- `POST /api/rooms/{roomId}/join`
- `GET /api/rooms/{roomId}`
- `GET /api/rooms/{roomId}/avatar-state`
- `POST /api/ai/public-question`
- `POST /api/ai/public-voice-question`
- `POST /api/audio/asr`
- `POST /api/audio/tts`
- `POST /api/vision/recognize`
- `GET /api/spots/{spotId}`
- `GET /api/spots/{spotId}/nearby`
- `POST /api/recommend/route`
- `GET /api/routes`
- `GET /api/routes/{routeId}`
- `POST /api/kb/upload`
- `GET /api/kb/docs`
- `POST /api/kb/rebuild`
- `POST /api/kb/test-query`
- `GET /api/dashboard/overview`
- `GET /api/dashboard/hot-questions`
- `GET /api/dashboard/hot-spots`
- `GET /api/dashboard/satisfaction`
- `GET /api/dashboard/system-metrics`

## 算法服务内部调试

算法服务可继续保留 `/v1` 前缀作为内部接口，例如 `/v1/orchestrate`、`/v1/vision/recognize`、`/v1/routes/recommend`。前端和产品联调文档不应使用这些路径。
