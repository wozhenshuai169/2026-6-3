# TTS / ASR 接口文档索引

下载日期：2026-07-16

本目录保存项目当前语音链路相关的离线文档。原始网页可能随厂商更新，正式上线前应再核对在线版本。

## 当前项目实际使用方式

### TTS：edge-tts

项目通过 Python 包 `edge-tts` 调用 Microsoft Edge 在线语音服务，不是 Azure Speech REST API。

- 项目实现：`app/providers/audio/dashscope.py`
- 本地文档：`TTS-edge-tts-README.md`
- 上游来源：https://github.com/rany2/edge-tts
- 主要调用：`edge_tts.Communicate(text, voice, rate=rate)`，然后迭代 `communicate.stream()` 保存音频块。
- 鉴权：当前方案不读取 Azure Speech API Key。
- 注意：这是依赖 Microsoft Edge 在线服务的第三方 Python 库，服务稳定性和接口兼容性不等同于正式 Azure Speech SLA。

### ASR：DashScope Paraformer

项目通过 DashScope REST API 提交 `paraformer-v2` 录音文件转写任务，然后轮询异步任务结果。

- 项目实现：`app/providers/audio/dashscope.py`
- API 参考：`ASR-Paraformer-REST-API.html`
- 使用指南：`ASR-non-realtime-user-guide.html`
- 官方来源：https://help.aliyun.com/zh/model-studio/paraformer-recorded-speech-recognition-restful-api
- 提交接口：`POST /api/v1/services/audio/asr/transcription`
- 查询接口：`/api/v1/tasks/{task_id}`
- 鉴权头：`Authorization: Bearer <DASHSCOPE_API_KEY>`
- 异步头：`X-DashScope-Async: enable`
- 关键输入：`model=paraformer-v2` 和 `input.file_urls`。

`file_urls` 中的音频必须能被 DashScope 从公网访问。本项目上传文件默认是本地 `/uploads/...` 地址，因此部署时需要配置 `PUBLIC_BASE_URL`，或把音频上传到 OSS 等公网存储。

## 补充参考：Microsoft Speech REST API

`TTS-Microsoft-Speech-REST-reference.html` 是微软官方 Azure Speech TTS REST 文档，供未来从 `edge-tts` 迁移到正式商业 API 时参考。它需要 Azure Speech 资源、区域端点和订阅密钥或访问令牌，当前项目没有调用这套接口。

- 官方来源：https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech

## 配置检查

完整语音链路至少需要：

- `DASHSCOPE_API_KEY`：推荐显式配置；当前代码也会回退使用 `VISION_API_KEY`。
- `PUBLIC_BASE_URL`：ASR 使用本地上传音频时必须是公网可访问的 HTTPS 根地址。
- `ENABLE_ASR=true`
- `ENABLE_TTS=true`
- Python 依赖 `edge-tts` 和 `httpx`。

不要把 API Key 写进示例、日志或提交到 Git。
