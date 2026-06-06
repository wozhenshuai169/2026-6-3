# A5 智能导游系统 — 联调说明

## 快速开始

### 1. 环境要求

- Python 3.10+
- Windows / Linux / macOS

### 2. 启动服务

**Windows:**
```bat
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh && ./start.sh
```

**手动启动:**
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. 配置 (.env)

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DEEPSEEK_API_KEY` | 百炼 API Key（LLM） | — |
| `DEEPSEEK_MODEL` | LLM 模型 | `qwen-plus` |
| `VISION_API_KEY` | 视觉 API Key | — |
| `VISION_MODEL` | 视觉模型 | `qwen-vl-plus` |
| `ENABLE_ASR` | 语音识别开关 | `true` |
| `ENABLE_TTS` | 语音合成开关 | `true` |
| `ENABLE_VISION` | 图片识景开关 | `true` |
| `ENABLE_RAG` | 知识检索开关 | `false` |
| `LOG_LEVEL` | 日志等级 | `INFO` |
| `REQUEST_TIMEOUT` | 请求超时（秒）| `60` |
| `ASR_TIMEOUT` | ASR 轮询超时 | `90` |

### 4. 服务地址

| 资源 | 地址 |
|------|------|
| API 服务 | `http://127.0.0.1:8000` |
| Swagger 文档 | `http://127.0.0.1:8000/docs` |
| 静态文件 | `http://127.0.0.1:8000/uploads/` |

## 架构

```
frontend
  │ POST /api/auth/register     → 用户注册
  │ POST /api/rooms              → 创建房间
  │ POST /api/rooms/{id}/join    → 加入房间
  │ GET  /api/rooms/{id}         → 房间状态
  │ GET  /api/rooms/{id}/avatar-state → 数字人状态
  │
  │ POST /api/ai/public-question      → 文本问答 (Qwen-Plus)
  │ POST /api/ai/public-voice-question→ 语音问答链路 (ASR→LLM→TTS)
  │
  │ POST /api/audio/asr    → 语音识别 (Paraformer-V2)
  │ POST /api/audio/tts    → 语音合成 (Edge-TTS)
  │
  │ POST /api/vision/recognize → 图片识景 (Qwen-VL-Plus)
  │ POST /api/recommend/route  → 路线推荐
  │
  ▼
  app/
  ├── api/        # API 路由
  ├── services/   # 业务逻辑
  ├── providers/  # 外部服务调用 (LLM / Vision / Audio / Map)
  ├── schemas/    # Pydantic 模型
  ├── core/       # 配置 / 日志
  └── middleware/  # FastAPI 中间件
```

## 异常处理

所有接口统一返回 JSON 错误：

```json
{
  "detail": "错误描述",
  "errorCode": "ERROR_CODE"
}
```

| 错误码 | 说明 |
|--------|------|
| `INTERNAL_ERROR` | 服务器内部错误 |
| `INVALID_PARAMETER` | 参数校验失败 |
| `TIMEOUT` | 请求超时 |

## 日志格式

```
22:30:15 | INFO    | rid=a1b2c3d4 | ep=/api/vision/recognize | [app.services.vision] | Vision took 1234ms
22:30:16 | WARNING | rid=a1b2c3d4 | ep=/api/audio/asr | [app.services.audio] | ASR format error: ...
22:30:16 | ERROR   | rid=e5f6g7h8 | ep=/api/ai/question | [app.providers.llm.deepseek] | LLM timeout (60s)
```

- `rid`: 请求 ID，贯穿整个请求链路
- `ep`: 当前接口路径
- 每个请求耗时自动记录
