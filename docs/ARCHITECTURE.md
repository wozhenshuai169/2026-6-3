# A5 智能导游系统架构

## 对外边界

`app.main:app` 是唯一对外 HTTP 和 WebSocket 服务。前端只调用 `/api/...`，并通过一次性 WebSocket 票据连接 `/ws/rooms/{roomId}`。`/v1/...` 与 `/api/v1/...` 不属于产品契约，也不能作为前端联调或验收入口。

```text
frontend-v2 / frontend-v4
  -> /api/... and /ws/rooms/{roomId}
  -> app/api: authentication, authorization, persistence, realtime delivery
  -> app/services/algorithm_facade.py
  -> src/ai_algorithm_service: decision, memory, resume, route scoring
  -> app/services: SQLite knowledge retrieval, audio and vision providers
  -> SQLite / configured model providers
```

## 主后端职责

`app/` 负责身份认证、角色权限、房间成员关系、SQLite 持久化、消息记录、知识库、上传文件、限流和 WebSocket 广播。算法服务不保存原始 Token、房间成员关系或公共消息。

房间、用户、会话、消息、知识库、反馈、运营事件和用户画像存放在 SQLite。游客画像只写入结构化标签，例如体力、同行人、兴趣和语言；原始对话不会写入画像表。

## 统一算法内核

`src/ai_algorithm_service/` 是产品实际使用的算法内核：

- `DecisionRouter`：公共/私人频道、打断、低 ASR 置信度和风险升级。
- `MemoryExtractor`：抽取可持久化的偏好标签。
- `TourExplanation`：基于回答摘要和现有讲解段生成续讲文本。
- `RouteRecommender`：以兴趣、时间、体力、同行人和当前位置的 `+3/+2/+2/+2/+1` 评分规则排序。
- `PrivateAssistant`：处理服务设施、离队和高风险安全问题。

`app/services/algorithm_facade.py` 将主后端已鉴权的房间状态和用户画像转换为算法请求，再把算法输出转换回现有 `/api` 响应字段。该适配层保证前端不需要因为算法升级修改请求或响应模型。

## 多模态与 RAG

文字问答和图片识别的引用来自 SQLite 知识库。未检索到证据时，系统返回明确的无资料提示，而不调用模型补充景区事实。图片 Provider 先给出识别结果，成功识别的景点再查询知识库并附带内部引用。

语音链路为：上传后的真实音频地址 -> ASR -> 统一决策和问答 -> TTS。真实 ASR Provider 不读取 `textHint`；它仅用于 Mock 开发模式。若上传文件为本地 `/uploads/...` 路径，部署环境需要设置 `PUBLIC_BASE_URL`，使外部 ASR Provider 可以读取该文件。

## 兼容与迁移

`archive/algorithm_service_legacy/` 是历史独立服务实现，仅用于兼容研究和旧接口排查，不参与产品 `/api` 调用。新功能不得在该目录继续扩展；产品算法逻辑统一进入 `src/ai_algorithm_service/` 并通过 `AlgorithmFacade` 调用。

公共频道中的私人需求不会写入房间公共消息。公共文本和语音问答仅在算法决策的回复频道为 `public` 时持久化并广播。安全和团长确认需求以算法事件形式返回，并记录运营事件供后端实时策略处理。

## 验证层次

- 规则测试：决策优先级、路线评分、续讲与画像抽取。
- API 集成测试：鉴权、持久化、公共消息隔离、上传、WebSocket 和响应兼容。
- 真实 Provider 测试：仅在配置真实 Key 和 Endpoint 后启用；Mock 测试不能作为模型准确率。

运行：

```bash
python -m pytest -q
python tools/verify_frontend_contracts.py
```
