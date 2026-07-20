# A5 智能导游系统

## Windows 一键启动（评委推荐）

需要 Python 3.11 或更高版本。双击 `start.bat`，或在项目目录运行：

```bat
start.bat
```

脚本会校验源码完整性，首次运行时创建 `.venv`，仅在依赖缺失或 `requirements.txt` 变更时安装依赖；随后执行数据、配置和功能自检，再以单 Worker 启动。默认端口 `8000` 被占用时会自动选择后续空闲端口，启动信息会显示实际入口。固定端口可运行 `start.bat 8010`。

## 手动启动

安装依赖并从示例配置创建本地 `.env`，先自检，再以单 Worker 启动：

```bash
python -m pip install -r requirements.txt
python tools/preflight.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

本版本使用 SQLite 和进程内 WebSocket/限流状态，不支持多 Worker。开发时可以将最后一个参数替换为 `--reload`，不要同时使用 `--reload` 和 `--workers`。

- 服务：`http://127.0.0.1:8000`
- Swagger：`http://127.0.0.1:8000/docs`
- OpenAPI：`http://127.0.0.1:8000/openapi.json`
- 存活检查：`GET /health/live`
- 就绪检查：`GET /health/ready`

前端只调用主后端 `/api/...`。根目录历史独立算法服务已归档到 `archive/algorithm_service_legacy/`；`/v1/...` 不属于 V4 前端契约。

## 外部能力与降级

`.env` 中的密钥不会提交到 Git。未配置某项凭据时，启动自检会显示 `WARN`，其余本地页面、知识检索和管理能力仍可运行；相关接口会返回明确的配置错误，不会伪造模型结果。

- `DEEPSEEK_API_KEY`：大模型问答
- `VISION_API_KEY`、`VISION_BASE_URL`、`VISION_MODEL`：图片识景和 Qwen ASR
- `DASHSCOPE_API_KEY`：可单独提供 Qwen ASR 凭据
- `MAP_API_KEY`：高德地图
- TTS 默认使用 Edge TTS，需要评委电脑可访问对应在线服务

本次重点完善并完整交付灵山胜境，同时保留项目原有的拈花湾等扩展知识和候选设施位置。未经核验的内容会降低来源等级并提示现场确认，不会因本次灵山完善而被删除。资料包质量审计与字段准入规则见 [docs/SOURCE_DATA_QUALITY.md](docs/SOURCE_DATA_QUALITY.md)。

## 认证

除注册、登录、访客会话和公开景点/路线外，HTTP 接口使用唯一长期认证方式：

```http
Authorization: Bearer <token>
```

Token 不得放入业务 JSON、FormData 或 URL。WebSocket 连接前调用 `POST /api/auth/ws-ticket` 换取 60 秒一次性票据，再连接 `/ws/rooms/{roomId}?ticket=...`。

## 数据与备份

默认数据库为 `data/app.db`。启动时自动执行版本迁移；检测到未版本化旧库时，会先通过 SQLite Backup API 生成 `data/backups/app-时间.db`。数据库、WAL、备份和上传文件均不提交 Git。

恢复时先停止后端，将当前数据库另行保存，再把选定备份复制为 `data/app.db` 后启动。不要在服务运行中直接覆盖数据库文件。

详细接口见 [docs/API.md](docs/API.md)，认证说明见 [docs/BACKEND_AUTH_API_2026-07-12.md](docs/BACKEND_AUTH_API_2026-07-12.md)。

## 验证

```bash
python -m pytest -q
python -m compileall -q app src
```

真实模型数据集验证通过已部署的主后端 `/api` 链路运行，不使用内部 `/v1`。录音样本和运行说明见 [test_data/real_model_validation/README.md](test_data/real_model_validation/README.md)。
