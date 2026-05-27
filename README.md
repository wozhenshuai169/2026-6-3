# AI Algorithm Service

面向团队旅游场景的算法编排服务，实现 `SPEC.md` 第一阶段要求：介入决策、公共 RAG 问答、私人助理、自然续讲、图文识景、路线推荐、记忆标签抽取、评测入口，以及 HTTP / WebSocket 联调接口。

## 运行

```bash
uvicorn ai_algorithm_service.api:app --app-dir src --reload
```

默认接口前缀为 `/v1`，健康检查：

```bash
curl http://127.0.0.1:8000/health
```

## 架构位置

```text
游客端 / 团长端
    -> 主后端 Backend
        -> AI Algorithm Service
            -> ModelProvider / ScenicDataAdapter / Local RAG Index
```

主后端维护房间、频道、导览状态和 WebSocket 连接；算法服务消费状态，返回结构化决策、自然语言回答和状态更新建议。

