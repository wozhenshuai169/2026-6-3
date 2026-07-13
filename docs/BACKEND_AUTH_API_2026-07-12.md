# 后端认证与授权

## Bearer 认证

受保护 HTTP 接口只接受 `Authorization: Bearer <token>`。Body、FormData 和 Query 中的长期 Token 均不兼容。Token 默认有效期由 `SESSION_TTL_SECONDS` 控制，退出登录会立即撤销当前会话；数据库只保存 Token 的 SHA-256 摘要。

账号密码使用带随机盐的 PBKDF2-SHA256 存储。公开注册只允许 `tourist` 和 `guide`，不能注册管理员。

## 认证端点

- `POST /api/auth/register`：真实账号注册。
- `POST /api/auth/login`：真实账号登录，包括管理员。
- `POST /api/auth/guest`：创建限时游客或团长体验会话。
- `GET /api/auth/me`：读取当前用户。
- `POST /api/auth/logout`：撤销当前 Bearer 会话。
- `POST /api/auth/ws-ticket`：房间成员换取 60 秒一次性 WebSocket 票据。

## 角色规则

- `tourist`：加入房间、提问、发普通消息、提交反馈。
- `guide`：可创建房间；房主可管理成员、景点和房间状态。
- `admin`：访问知识库和运营看板；账号只通过环境变量首次引导创建。

设置 `ADMIN_USER_NAME` 和 `ADMIN_PASSWORD` 后首次启动，管理员即可通过 `/api/auth/login` 登录。生产或终验环境必须修改 `.env.example` 中的示例密码。

## WebSocket

1. 使用 Bearer 调用 `POST /api/auth/ws-ticket`，Body 为 `{"roomId":"..."}`。
2. 使用响应中的票据连接 `/ws/rooms/{roomId}?ticket=<one-time-ticket>`。
3. 票据只可消费一次，超时或复用均以 WebSocket 4401 拒绝。
