# A5 团队旅游实时群组导览 AI 数字人系统 — 架构总览

## 系统拓扑

```
前端（游客端 / 团长端）
        │
        v
┌─────────────────────────┐
│   主后端 Backend         │  port 8000
│   app/                   │
│   - 房间管理              │
│   - 用户注册 & 认证        │
│   - 频道管理              │
│   - 状态维护              │
│   - WebSocket 连接管理    │
└──────────┬──────────────┘
           │ HTTP / WebSocket
           v
┌─────────────────────────┐
│   AI Algorithm Service   │  port 8001
│   algorithm_service/     │
│   - Tour AI Orchestrator │
│   - DecisionRouter       │
│   - ScenicRAG            │
│   - TourExplanation      │
│   - PrivateAssistant     │
│   - VisionRecognizer     │
│   - RouteRecommender     │
│   - MemoryExtractor      │
└──────────┬──────────────┘
           │
           v
   模型 Provider / 向量库 / 景区数据适配层
   (DeepSeek, Qwen, Milvus, 景区 API 等)
```

---

## 一、主后端 Backend（port 8000）

### 目录结构

```
app/
├── main.py              # FastAPI 入口
├── api/
│   ├── rooms.py         # 房间 CRUD 路由
│   ├── users.py         # 用户注册路由
│   └── ai.py            # AI 公共问答路由（后续迁至 algorithm_service）
├── schemas/
│   ├── rooms.py         # 房间 Pydantic 模型
│   ├── users.py         # 用户 Pydantic 模型
│   └── ai.py            # AI Pydantic 模型
├── services/
│   ├── rooms.py         # 房间业务逻辑 + rooms{} 内存字典
│   ├── users.py         # 用户业务逻辑 + users{} 内存字典
│   └── ai.py            # AI 业务逻辑（临时桥接）
├── models/              # 数据库 ORM（待接入）
└── core/                # 配置（待扩展）
```

### 接口清单

| 方法 | 路径 | 作用 | 认证 |
|------|------|------|------|
| POST | `/api/auth/register` | 用户注册，返回 token | 无 |
| POST | `/api/rooms` | 创建导览房间 | Token（Body） |
| GET | `/api/rooms/{roomId}` | 查询房间状态 | 无（暂） |
| POST | `/api/rooms/{roomId}/join` | 加入房间 | Token（Body） |
| POST | `/api/rooms/{roomId}/current-spot` | 更新当前讲解点 | 无（暂） |
| POST | `/api/ai/public-question` | AI 公共问答（→迁移至 algorithm_service） | 无（暂） |

### 当前数据模型

**房间（rooms{}）：**
```json
{
  "roomId": "uuid",
  "leaderId": "uuid",
  "members": [{"userId": "uuid", "userName": "string"}],
  "currentSpot": "spot_id",
  "status": "active"
}
```

**用户（users{}）：**
```json
{
  "token": {"userId": "uuid", "userName": "string", "password": "string"}
}
```

### 状态说明
- 数据存于内存字典，服务重启丢失
- 调用链：api → schemas（校验）→ services（业务逻辑）
- 尚未接入数据库（models/ 为空）

---

## 二、AI Algorithm Service（port 8001）

### 定位

算法服务是主后端的独立算法层，**不维护房间主状态**。主后端将导览上下文随请求传入，算法服务消费后返回决策/回答/状态更新建议。

### 目录结构

```
algorithm_service/
├── main.py
├── api/
│   ├── orchestrator.py   # 8 个 HTTP 端点 + 统一调度入口
│   └── ws.py             # 2 个 WebSocket 流式端点
├── schemas/
│   ├── decision.py
│   ├── rag.py
│   ├── explanation.py
│   ├── private_assistant.py
│   ├── vision.py
│   ├── route.py
│   └── memory.py
├── services/
│   ├── orchestrator.py          # Tour AI Orchestrator 调度器
│   ├── decision_router.py       # 介入决策
│   ├── scenic_rag.py            # 公共知识 RAG
│   ├── tour_explanation.py      # 讲解生成 + 续讲
│   ├── private_assistant.py     # 私人导览助手
│   ├── vision_recognizer.py     # 图片识景
│   ├── route_recommender.py     # 路线推荐
│   └── memory_extractor.py      # 游客记忆标签
└── core/
    └── config.py
```

### HTTP 接口（统一响应格式 `{code, message, data}`）

| 端点 | 模块 | 输入关键字段 | 输出关键字段 |
|------|------|-------------|-------------|
| `POST /api/v1/decision` | DecisionRouter | roomId, userId, event, context | shouldIntervene, channel(public/private/none), shouldInterrupt, reason |
| `POST /api/v1/rag` | ScenicRAG | roomId, userId, question, currentSpot, context | answer, sources[], confidence, stateUpdate |
| `POST /api/v1/explanation` | TourExplanation | roomId, spotId, spotName, style, context | explanation, continuation, ttsText, stateUpdate |
| `POST /api/v1/private-assistant` | PrivateAssistant | roomId, userId, question, context | answer, needLeaderAuth, notification, stateUpdate |
| `POST /api/v1/vision` | VisionRecognizer | roomId, userId, imageUrl, context | sceneName, description, tags[], stateUpdate |
| `POST /api/v1/route-recommend` | RouteRecommender | roomId, currentSpot, preferences[], context | recommendedRouteId, reason, alternatives[], stateUpdate |
| `POST /api/v1/memory-extract` | MemoryExtractor | userId, dialogue, context | tags[], interests[], summary |
| `POST /api/v1/orchestrate` | Tour AI Orchestrator | intent, + 各模块字段 | 根据 intent 路由到对应模块 |

### WebSocket 端点

| 端点 | 作用 | 流式输出 |
|------|------|---------|
| `WS /ws/explanation/{roomId}` | 公共讲解推送 | 讲解文本块 → TTS 文本 → 续讲建议 → done |
| `WS /ws/answer/{roomId}/{userId}` | 回答流式推送 | 查询中 → 答案块 → done |

### 模块职责

| 模块 | 职责 | 当前状态 |
|------|------|---------|
| **Tour AI Orchestrator** | 统一入口，按 intent 路由到下游模块 | Mock |
| **DecisionRouter** | 判断 AI 是否介入、公共/私人频道、是否打断当前讲解 | Mock — 按 event 类型规则判断 |
| **ScenicRAG** | 基于知识库的公共知识问答，返回带来源引用的答案 | Mock |
| **TourExplanation** | 生成讲解文本 + 自然续讲建议 + TTS 语音文本 | Mock — 支持 standard/storytelling/kid_friendly 风格 |
| **PrivateAssistant** | 私人导览问题处理，判断是否需要团长授权 | Mock |
| **VisionRecognizer** | 图片识景，返回景点名称+描述+标签 | Mock |
| **RouteRecommender** | 基于当前位置和偏好推荐路线 | Mock — 返回推荐 ID + 备选路线 |
| **MemoryExtractor** | 从对话中抽取游客标签/兴趣/摘要 | Mock |

---

## 三、调用流程示例

### 场景：游客在太和殿前提问

```
1. 主后端收到用户消息 → POST /api/ai/public-question（当前临时桥接）
   ↓（后续改为）
   
2. 主后端 → POST algorithm_service:8001/api/v1/decision
   {event: "user_question", roomId, userId, context:{currentSpot, ...}}
   ← {shouldIntervene: true, channel: "public", shouldInterrupt: false}

3. 主后端 → POST algorithm_service:8001/api/v1/rag
   {question: "这个建筑是什么时候建的？", currentSpot: "太和殿", ...}
   ← {answer: "...", sources: [...], confidence: 0.85}

4. 主后端通过 WebSocket 推送给房间内所有成员
```

### 场景：到达新讲解点

```
1. 主后端检测到位置变更 → POST algorithm_service:8001/api/v1/decision
   {event: "spot_reached", ...}
   ← {shouldIntervene: true, channel: "public", shouldInterrupt: true}

2. 主后端 → POST algorithm_service:8001/api/v1/explanation
   {spotId: "spot_003", spotName: "中和殿", style: "storytelling"}
   ← {explanation: "...", continuation: "...", ttsText: "..."}

3. 主后端通过 WS /ws/explanation/{roomId} 流式推送讲解
```

---

## 四、开发程度总览

| 模块 | api | schemas | services | models |
|------|-----|---------|----------|--------|
| 主后端 rooms | ✅ | ✅ | ✅ | ⬜ |
| 主后端 users | ✅ | ✅ | ✅ | ⬜ |
| 主后端 ai（桥接） | ✅ | ✅ | ✅ | ⬜ |
| 算法 DecisionRouter | ✅ | ✅ | ✅ (Mock) | N/A |
| 算法 ScenicRAG | ✅ | ✅ | ✅ (Mock) | N/A |
| 算法 TourExplanation | ✅ | ✅ | ✅ (Mock) | N/A |
| 算法 PrivateAssistant | ✅ | ✅ | ✅ (Mock) | N/A |
| 算法 VisionRecognizer | ✅ | ✅ | ✅ (Mock) | N/A |
| 算法 RouteRecommender | ✅ | ✅ | ✅ (Mock) | N/A |
| 算法 MemoryExtractor | ✅ | ✅ | ✅ (Mock) | N/A |
| 算法 WebSocket | ✅ | N/A | ✅ (Mock) | N/A |

---

## 五、算法设计师接入指南

### 需要真实实现的模块（按优先级）

1. **ScenicRAG** — 接入向量库 + 大模型，替换 `services/scenic_rag.py` 的 `answer()` 函数
2. **TourExplanation** — 接入大模型流式输出，替换 `services/tour_explanation.py`
3. **DecisionRouter** — 细化决策规则，可接入小模型做意图分类
4. **PrivateAssistant** — 接入大模型 + 团长通知逻辑
5. **VisionRecognizer** — 接入 Qwen-VL 等多模态模型
6. **RouteRecommender** — 接入景区路线数据
7. **MemoryExtractor** — 接入大模型做对话摘要和标签抽取

### 接口契约

- 所有接口的请求/响应 Schema 定义在 `schemas/` 下，**不可修改字段名和类型**
- services 层函数签名已确定，算法设计师只需替换函数体
- 响应中 `stateUpdate` 字段用于向主后端传递状态变更建议
- 模拟数据即为期望返回格式的示例

### 下游依赖接口（需算法设计师自行对接）

| 依赖 | 用途 | 预留位置 |
|------|------|---------|
| 大模型 API（DeepSeek/Qwen/...） | 问答、讲解、摘要 | services/ 各模块 |
| 向量数据库（Milvus/Chroma/...） | 景区知识检索 | services/scenic_rag.py |
| Qwen-VL | 图片识景 | services/vision_recognizer.py |
| 景区数据 API | 路线、景点信息 | services/route_recommender.py |
| ASR/TTS | 语音交互 | 新增 services/voice_adapter.py |
