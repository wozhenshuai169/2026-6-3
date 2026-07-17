# A5 智能导游系统 - 联调说明

## 统一入口

主后端是前端唯一入口：

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- 前端只请求 `/api/...`
- `/uploads/...` 用于访问 TTS 音频和知识库上传文件
- 历史算法服务已归档，前端和主后端都不调用 `/v1/...`；产品算法统一经 `app/services/algorithm_facade.py` 调用

## 服务地址

- API 服务：`http://127.0.0.1:8000`
- Swagger：`http://127.0.0.1:8000/docs`
- OpenAPI：`http://127.0.0.1:8000/openapi.json`
- 静态文件：`http://127.0.0.1:8000/uploads/`

## 核心联调链路

```text
注册游客
  -> POST /api/auth/register
创建房间
  -> POST /api/rooms
加入房间
  -> POST /api/rooms/{roomId}/join
更新当前景点
  -> POST /api/rooms/{roomId}/current-spot
文本问答
  -> POST /api/ai/public-question
播放音频
  -> GET /uploads/tts/{fileName}
读取数字人状态
  -> GET /api/rooms/{roomId}/avatar-state
查看大屏统计
  -> GET /api/dashboard/overview
```

## 已开放接口

### 用户与房间

- `POST /api/auth/register`
- `POST /api/rooms`
- `POST /api/rooms/{roomId}/join`
- `GET /api/rooms/{roomId}`
- `POST /api/rooms/{roomId}/current-spot`
- `GET /api/rooms/{roomId}/avatar-state`

### AI 与音频

- `POST /api/ai/public-question`
- `POST /api/ai/public-voice-question`
- `POST /api/audio/asr`
- `POST /api/audio/tts`

`public-question` 支持 `needAudio`。当 TTS 失败时，接口仍返回 `answer`，并返回 `audioUrl=null`、`duration=0`、`warning`。

### 图片识景、景点和路线

- `POST /api/vision/recognize`
- `GET /api/spots/{spotId}`
- `GET /api/spots/{spotId}/nearby`
- `POST /api/recommend/route`
- `GET /api/routes`
- `GET /api/routes/{routeId}`

### 知识库

- `POST /api/kb/upload`
- `GET /api/kb/docs`
- `POST /api/kb/rebuild`
- `POST /api/kb/test-query`

`/api/kb/rebuild` 表示刷新知识库检索缓存；第一版基于关键词检索，后续可替换为向量检索。

### 实时运营事件

- `GET /api/operation-events?scenicAreaId=scenic_001`
- `POST /api/operation-events`（admin）
- `PATCH /api/operation-events/{eventId}`（admin）

团长或运营人员发布封路、天气、人流、设施关闭事件后，问答检索会优先引用仍在有效期内的公告。语音 ASR 依赖外部服务读取上传音频时，必须把 `PUBLIC_BASE_URL` 配置为该后端可被服务商访问的 HTTPS 地址；本地 `127.0.0.1` 仅适合文字、图片和 TTS 验证。

### 数据大屏

- `GET /api/dashboard/overview`
- `GET /api/dashboard/hot-questions`
- `GET /api/dashboard/hot-spots`
- `GET /api/dashboard/satisfaction`
- `GET /api/dashboard/system-metrics`
