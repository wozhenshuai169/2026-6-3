# 主后端 API 契约

基础地址：`http://127.0.0.1:8000`。除明确标注公开的端点外，请发送 `Authorization: Bearer <token>`。

统一错误响应：

```json
{"detail":"错误说明","errorCode":"STABLE_CODE","requestId":"request-id"}
```

限流响应为 `429`，并带 `Retry-After`。Provider 不可用返回 `502/503`；Mock 降级通过业务响应 `warning` 和根路径健康信息显式标识。

## 认证

| 方法 | 路径 | 认证 | 说明 |
|---|---|---|---|
| POST | `/api/auth/register` | 公开 | `userName/password/role(tourist|guide)` |
| POST | `/api/auth/login` | 公开 | 真实账号登录 |
| POST | `/api/auth/guest` | 公开 | `displayName/role(tourist|guide)` |
| GET | `/api/auth/me` | Bearer | 当前用户 |
| POST | `/api/auth/logout` | Bearer | 撤销当前会话 |
| POST | `/api/auth/ws-ticket` | Bearer + 房间成员 | `roomId`，返回一次性票据 |

## 房间与消息

| 方法 | 路径 | 权限/说明 |
|---|---|---|
| POST | `/api/rooms` | guide/admin；创建者成为房主 |
| GET | `/api/rooms/{roomId}` | 房间成员 |
| POST | `/api/rooms/{roomId}/join` | active 房间；空 JSON Body |
| DELETE | `/api/rooms/{roomId}/members/me` | 成员退出；未结束房间的房主需先转移 |
| DELETE | `/api/rooms/{roomId}/members/{userId}` | 房主移除成员 |
| PATCH | `/api/rooms/{roomId}/leader` | 房主；Body `userId` |
| POST | `/api/rooms/{roomId}/current-spot` | 房主且房间 active |
| PATCH | `/api/rooms/{roomId}/status` | 房主；`active/paused/ended`，ended 不可恢复 |
| GET | `/api/rooms/{roomId}/avatar-state` | 房间成员 |
| GET | `/api/rooms/{roomId}/messages` | 房间成员；`limit/cursor` |
| POST | `/api/rooms/{roomId}/messages` | 房间成员；`content/type(user|broadcast)` |

WebSocket：`/ws/rooms/{roomId}?ticket=<one-time-ticket>`。客户端事件支持 `ping` 和 `message`；服务端事件包括 `room.connected`、`room.message`、`room.members`、`room.leader`、`room.spot`、`room.status`、`pong`、`error`。

## AI、音频与视觉

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/ai/public-question` | active 房间公共问答并落库 |
| POST | `/api/ai/public-voice-question` | 语音公共/私有问答 |
| POST | `/api/audio/upload` | multipart：`file/roomId/userId/channel` |
| POST | `/api/audio/asr` | ASR |
| POST | `/api/audio/tts` | TTS |
| POST | `/api/vision/recognize` | 限制 JPEG/PNG/WebP 与解码大小 |
| POST | `/api/recommend/route` | 路线推荐 |

音频上传允许 WAV、MP3、WebM、OGG、M4A，校验扩展名、MIME、文件签名和大小，使用随机文件名原子落盘。

## 知识库（admin）

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/kb/upload` | multipart TXT/Markdown/JSON/PDF |
| GET | `/api/kb/docs` | 文档列表与状态 |
| GET | `/api/kb/docs/{docId}` | 文档详情与分块数 |
| DELETE | `/api/kb/docs/{docId}` | 删除文件、元数据和索引 |
| POST | `/api/kb/rebuild` | 返回成功/失败数量 |
| POST | `/api/kb/test-query` | FTS5 trigram 中文检索 |

## 反馈、看板与公共目录

- `POST /api/feedback`：房间成员提交或更新 `roomId/userId/score(1..5)/scene`。
- admin 看板：`/api/dashboard/overview`、`hot-questions`、`hot-spots`、`satisfaction`、`system-metrics`。
- 公共目录：`GET /api/spots/{spotId}`、`GET /api/spots/{spotId}/nearby`、`GET /api/routes`、`GET /api/routes/{routeId}`。
- 健康检查：`GET /health/live`、`GET /health/ready`。

Swagger 和 OpenAPI 是字段级最终依据：`/docs`、`/openapi.json`。
