# 后端持久化与实时通信

## SQLite

数据库路径由 `DATABASE_PATH` 配置，默认 `data/app.db`。启动 lifespan 会启用 WAL、外键、10 秒 busy timeout，并执行 `schema_migrations` 中尚未应用的事务迁移。

未版本化旧库升级前会通过 SQLite Backup API 写入 `data/backups/`。迁移失败会回滚当前版本，已有数据库和上传文件不会被删除。服务每五分钟清理过期会话、已消费票据、可删除的访客账号和残留 `.part` 文件。

持久化内容包括用户、会话、房间、成员、消息、知识文档与分块、反馈、运营事件和 WebSocket 临时票据。

## 消息分页

`GET /api/rooms/{roomId}/messages?limit=100&cursor=...` 使用不透明稳定游标，排序键为毫秒时间戳与消息 ID。客户端应原样传回 `nextCursor`，不要解析或自行构造。

加入、退出、景点更新、状态变化、广播、用户消息和 AI 公共问答均持久化或实时广播；已结束房间只读。

算法触发的高风险和团长确认事件以 `room.alert` 只发送给房主连接，不会进入公共消息历史或广播给普通成员。

## 单实例约束

WebSocket 连接表和限流窗口位于当前进程内，因此必须使用一个 Uvicorn Worker。多实例部署需要先迁移到共享数据库/消息系统和分布式限流，本版本不宣称支持该场景。
