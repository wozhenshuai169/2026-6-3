# AI Algorithm Service

面向团队旅游场景的算法编排服务，实现 `SPEC.md` 第 2 周要求：介入决策、公共 RAG 问答、私人助理、自然续讲、固定图库识景 V0.1、可解释路线推荐、Mock ASR/TTS 语音链路、记忆标签抽取、评测入口，以及 HTTP / WebSocket 联调接口。

## 运行

```bash
uvicorn ai_algorithm_service.api:app --app-dir src --reload
```

默认接口前缀为 `/v1`，健康检查：

```bash
curl http://127.0.0.1:8000/health
```

## 主要接口

- `POST /v1/orchestrate`：文本/图片统一编排入口。
- `POST /v1/voice/asr`：Mock ASR，支持 `wav` / `mp3`。
- `POST /v1/voice/tts`：Mock TTS，返回导游音色音频元数据。
- `POST /v1/voice/orchestrate`：ASR -> 算法编排 -> TTS 语音问答链路。
- `POST /v1/vision/recognize`：固定图库识景，返回景点、视觉特征和 RAG 讲解。
- `POST /v1/routes/recommend`：路线推荐，返回可解释 `scoreBreakdown`。
- `POST /v1/evaluation/run`：运行演示评测集。

## 架构位置

```text
游客端 / 团长端
    -> 主后端 Backend
        -> AI Algorithm Service
            -> ModelProvider / ScenicDataAdapter / Local RAG Index
```

主后端维护房间、频道、导览状态和 WebSocket 连接；算法服务消费状态，返回结构化决策、自然语言回答和状态更新建议。
