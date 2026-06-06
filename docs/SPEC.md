# 第 2 周算法任务需求与当前实现对齐说明

## 1. 文档目的

本文档用于明确第 2 周算法任务、当前代码实现对齐情况、缺口和推荐推进顺序。

当前项目已经存在 `ai_algorithm_service` 服务骨架，包含介入决策、RAG、私人助理、自然续讲、图片识景占位、路线推荐、记忆抽取、评测入口、HTTP / WebSocket 接口。第 2 周重点不是重新设计项目，而是把已有骨架补成可比赛演示的真实可运行服务。

## 2. 当前实现概览

当前代码位置：

- `src/ai_algorithm_service/api.py`：FastAPI HTTP / WebSocket 接口；
- `src/ai_algorithm_service/orchestrator.py`：算法编排入口；
- `src/ai_algorithm_service/decision.py`：规则优先介入决策器；
- `src/ai_algorithm_service/rag.py`：轻量关键词式 RAG；
- `src/ai_algorithm_service/private_assistant.py`：私人助理和团长通知；
- `src/ai_algorithm_service/explanation.py`：讲解段落和续讲；
- `src/ai_algorithm_service/vision.py`：图片识景占位实现；
- `src/ai_algorithm_service/routes.py`：路线推荐；
- `src/ai_algorithm_service/memory.py`：游客记忆标签抽取；
- `src/ai_algorithm_service/evaluation.py`：评测入口；
- `tests/test_algorithm_service.py`：核心行为测试。

当前服务已经具备以下接口：

- `GET /health`
- `POST /v1/decision`
- `POST /v1/orchestrate`
- `POST /v1/rag/query`
- `POST /v1/private-assistant`
- `POST /v1/vision/recognize`
- `POST /v1/routes/recommend`
- `POST /v1/memory/extract`
- `POST /v1/evaluation/run`
- `WS /ws/rooms/{room_id}/stream`

## 3. 第 2 周算法需求

第 2 周算法侧需要完成：

1. ASR / TTS 对接；
2. 图片识景 V0.1；
3. 路线推荐算法 V0.1；
4. 介入决策器优化；
5. 续讲能力优化。

目标是支持比赛演示中的多模态交互、智能问答、路线推荐、语音基本功能，并能和景区管理数据接口预留对接。

## 4. 对齐情况总表

| 任务 | 当前实现状态 | 对齐结论 | 第 2 周建议 |
| --- | --- | --- | --- |
| ASR 语音转文字 | 未实现 | 不对齐 | 新增语音适配模块 |
| TTS 文字转语音 | 未实现 | 不对齐 | 新增 TTS 封装和兜底 |
| 语音问答链路 | 未实现 | 不对齐 | ASR -> orchestrate -> TTS |
| 音频格式统一 | 未实现 | 不对齐 | 支持 wav / mp3 上传 |
| 图片识景 | 有占位 | 部分对齐 | 从关键词匹配升级到 Qwen-VL 或固定图片库 |
| 图片识别 + RAG 讲解 | 已有基础链路 | 部分对齐 | 保留现链路，替换识别层 |
| 路线推荐 | 已实现规则推荐 | 基本对齐 | 补齐景点标签、时间、体力、老人儿童权重 |
| 介入决策器 | 已实现规则优先 | 基本对齐 | 增加 ASR 置信度、公共频道私人问题、讲解打断细则 |
| 续讲能力 | 已有过渡语 | 基本对齐 | 增强自然衔接，避免机械续读 |
| 失败兜底 | 部分存在 | 部分对齐 | 补齐 ASR/TTS/识图/模型超时兜底 |

## 5. ASR / TTS 对接

### 5.1 需求

第 2 周需要支持：

- ASR 语音转文字；
- TTS 文字转语音；
- 语音问答链路封装；
- 音频文件格式统一；
- 失败兜底。

第一版支持：

- `wav` / `mp3` 上传；
- 普通话识别；
- 中文 TTS；
- 固定一个导游音色。

暂时不做：

- 多人说话人分离；
- 复杂户外降噪；
- 实时流式识别；
- 情绪语音合成；
- 数字人口型同步。

### 5.2 当前对齐情况

当前代码没有 ASR / TTS 模块，也没有音频上传接口。

已具备的基础：

- `orchestrator.handle()` 已经可以处理文本；
- WebSocket 已经支持回答文本流；
- 后续只需要把 ASR 输出的文本接入现有 `AlgorithmRequest.text`。

### 5.3 推荐实现

新增模块：

- `voice.py`
- `VoiceAdapter`
- `ASRResult`
- `TTSResult`

推荐链路：

```text
音频上传
-> 统一格式检查
-> ASR 普通话识别
-> 得到 text + confidence
-> AlgorithmRequest(text=识别文本)
-> orchestrator.handle()
-> 得到 answer
-> TTS 合成中文导游音色
-> 返回文本结果 + 音频 URL / 音频文件路径
```

ASR 输出建议：

```json
{
  "text": "我想去厕所",
  "confidence": 0.82,
  "language": "zh-CN",
  "format": "wav"
}
```

TTS 输出建议：

```json
{
  "audioUrl": "/static/tts/demo_001.mp3",
  "voice": "guide_female_zh",
  "format": "mp3",
  "durationMs": 3200
}
```

失败兜底：

- ASR 置信度过低：追问确认；
- ASR 失败：返回“我没有听清，可以再说一遍或改用文字输入”；
- TTS 失败：保留文字回答，不阻塞导览；
- 音频格式不支持：提示只支持 `wav / mp3`。

## 6. 图片识景 V0.1

### 6.1 需求

第一版可以先准备：

- 5 个景点；
- 每个景点 5-10 张示例图；
- 识别后返回景点名称、置信度、视觉特征和讲解。

识别输出：

```json
{
  "spotName": "钟楼",
  "confidence": 0.87,
  "visualFeatures": ["木结构", "重檐", "钟鼓建筑"]
}
```

然后调用 RAG：

```text
识别出景点
-> 检索该景点知识库
-> 生成讲解词
```

### 6.2 当前对齐情况

当前 `vision.py` 只做关键词匹配：

- `imageUrl` 或文本里包含 `bell`、`zhonglou`、`钟楼` 时识别为钟楼；
- 识别后已经会调用 `rag.query()`；
- 未真正接入 Qwen-VL；
- 未返回 `visualFeatures`；
- 未支持固定景点图片库匹配。

结论：链路方向正确，但识别能力只是占位。

### 6.3 推荐实现

优先方案：

```text
Qwen-VL 识别图片内容
-> 输出景点候选、置信度、视觉特征
-> ScenicRAG 检索该景点资料
-> 生成自然讲解
```

备选方案：

```text
固定景点图片库匹配
-> 每个景点准备 5-10 张图
-> 用文件名 / metadata / 简单 embedding 匹配
-> 作为 Qwen-VL 失败兜底
```

建议保留双方案：

- 比赛演示时，固定图片库更稳定；
- 展示创新时，Qwen-VL 更能体现多模态能力；
- 两者结合可以降低模型误识别风险。

## 7. 路线推荐算法 V0.1

### 7.1 需求

第一版不做复杂地图路径规划，采用规则 + 打分。

输入因素：

- 兴趣偏好；
- 游览时间；
- 体力水平；
- 是否带老人；
- 是否带儿童；
- 是否想少走路；
- 是否想深度讲解；
- 当前景点。

景点标签示例：

```json
{
  "spotId": "spot_002",
  "spotName": "主展厅",
  "tags": ["历史", "建筑", "室内"],
  "suggestedStayMinutes": 20,
  "walkingDifficulty": "low",
  "suitableForChildren": true,
  "suitableForElderly": true
}
```

打分规则：

- 兴趣匹配：`+3`
- 时间可控：`+2`
- 体力适配：`+2`
- 老人儿童友好：`+2`
- 距离较短：`+1`

### 7.2 当前对齐情况

当前 `routes.py` 已经实现：

- 基于 `profile.interests`；
- 基于 `memoryTags.interest`；
- 基于 `memoryTags.routePreference`；
- 低体力加 `less_walking`；
- 老人儿童加 `family_friendly`；
- 当前景点在路线中加分；
- 返回推荐理由。

缺口：

- 当前分数是轻量归一化，不是明确的 `+3/+2/+2/+2/+1`；
- 数据侧是否有每个景点的 `suggestedStayMinutes`、`walkingDifficulty`、`suitableForChildren` 等字段需要确认；
- 未显式处理“深度讲解”“游览时间”。

### 7.3 推荐实现

保留当前结构，调整评分为可解释加分制：

```text
score = interestScore + timeScore + staminaScore + companionScore + distanceScore
```

输出必须包含：

- 推荐路线；
- 路线包含景点；
- 总预计时间；
- 体力难度；
- 推荐理由；
- 命中的用户偏好。

## 8. 介入决策器优化

### 8.1 需求

第 2 周新增判断：

- ASR 置信度过低 -> 追问确认；
- 公共频道中的私人问题 -> 建议转私人频道；
- 安全 / 身体不适问题 -> 提醒团长；
- 普通闲聊 -> 不介入；
- 当前 AI 正在讲解 -> 判断是否打断。

示例输入：

```json
{
  "text": "我想去厕所",
  "channel": "public",
  "aiStatus": "explaining"
}
```

期望输出：

```json
{
  "decision": "private_reply",
  "replyChannel": "private",
  "shouldInterrupt": false,
  "needLeaderConfirm": false,
  "reason": "该问题属于个人服务设施查询，不适合公共播报"
}
```

### 8.2 当前对齐情况

当前 `decision.py` 已支持：

- 安全 / 身体不适 / 走失 -> `emergency_alert`；
- 离队 -> `notify_leader`；
- 私人问题 -> `private_reply`；
- 公共知识问题 -> `interrupt_and_answer` 或 `public_reply`；
- 闲聊 -> `ignore`；
- 图片 -> `vision_recognize`；
- 讲解中公共问题 -> `needInterrupt=True`。

缺口：

- `AlgorithmRequest` 里没有 ASR 置信度字段；
- 输出字段名是 `channel`、`needInterrupt`、`needLeaderNotify`，不是 `replyChannel`、`shouldInterrupt`、`needLeaderConfirm`；
- 当前私人问题会直接进入私人回复，但还可以补充“建议转私人频道”的用户提示；
- GPS 信号问题、路线封闭、突发天气可以继续扩充关键词。

### 8.3 推荐实现

新增字段：

```json
{
  "asrConfidence": 0.82,
  "inputMode": "voice"
}
```

新增决策：

- ASR 置信度 `< 0.6`：`private_reply` 或 `public_reply`，`nextAction="ask_clarification"`；
- 公共频道私人问题：`private_reply`，同时返回 `events=[{"type": "suggest_private_channel"}]`；
- GPS 信号异常：不依赖 GPS，要求游客补充标志物；
- 路线封闭 / 突发天气：通知团长并以景区公告为准。

## 9. 续讲能力优化

### 9.1 需求

第二周续讲要做到：

```text
回答游客问题
-> 用一句过渡语连接
-> 回到原讲解段落
```

示例：

```text
这个建筑始建于明代，清代曾进行过修缮。了解了它的年代背景后，我们再看它屋顶上的装饰纹样，这些纹样正体现了当时地方工艺的特点。
```

### 9.2 当前对齐情况

当前 `explanation.py` 已经具备：

- `resume_after_answer()`；
- 根据问题关键词生成不同过渡语；
- 返回 `resumeText`；
- 测试里已检查 `resumeText` 存在。

缺口：

- 目前续讲文本仍是模板拼接；
- 过渡语类型较少；
- 没有把 RAG 回答和下一段讲解进行语义融合；
- 没有检测是否重复原文或衔接生硬。

### 9.3 推荐实现

第二周建议分两步：

1. 先扩展模板：
   - 年代 / 历史；
   - 建筑结构；
   - 工艺细节；
   - 路线安排；
   - 服务设施；
   - 图片识别；
   - 游客没听懂。

2. 再接 LLM 改写：
   - 输入：游客问题、回答摘要、当前段落、下一段落；
   - 输出：一句自然过渡 + 续讲文本；
   - 限制：不引入新事实，不改变知识库结论。

## 10. 推荐推进顺序

第 2 周建议顺序：

1. 补 `SPEC.md` 和接口字段，先统一团队预期；
2. 新增 ASR / TTS 适配层，但先允许 mock；
3. 给 `AlgorithmRequest` 增加 `inputMode`、`asrConfidence`；
4. 优化 `DecisionRouter`，处理低置信度语音和公共频道私人问题；
5. 把 `VisionRecognizer` 从关键词占位升级为 Qwen-VL Provider + 固定图片库兜底；
6. 调整路线推荐为明确加分制；
7. 扩展续讲模板，再预留 LLM 改写；
8. 扩展 EvaluationHarness，加入 ASR、识图、推荐、续讲自然度样本；
9. 补充测试，确保原有第一阶段行为不回退。

## 11. 当前最关键缺口

优先级最高的缺口：

1. `SPEC.md` 原本为空，团队缺少第 2 周检查基线；
2. ASR / TTS 完全未实现；
3. 图片识景只是关键词占位，没有真正多模态；
4. 介入决策缺少 ASR 置信度输入；
5. 路线推荐打分没有完全按需求的可解释加分制；
6. 续讲有基础，但自然度仍需增强。

## 12. 验收标准

第 2 周结束时至少满足：

- 支持 `wav / mp3` 音频输入；
- ASR 输出文本和置信度；
- TTS 可生成中文导游音色音频，失败时保留文字；
- 低 ASR 置信度会追问确认；
- 公共频道里的私人问题不会公共播报；
- 安全、身体不适、走失、离队、路线封闭会升级；
- 5 个景点图片可识别；
- 图片识别后能调用 RAG 生成讲解；
- 推荐路线能解释分数来源；
- 打断问答后能自然续讲；
- EvaluationHarness 覆盖主要指标。
