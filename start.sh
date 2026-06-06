#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════
# A5 智能导游系统 —— Linux/Mac 启动脚本
# ═══════════════════════════════════════════════════════
set -e

echo ""
echo "========================================"
echo "  A5 智能导游系统 v1.0.0"
echo "========================================"
echo ""

# Python 检查
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] 未找到 python3"
    exit 1
fi

# 虚拟环境
if [ ! -d "venv" ]; then
    echo "[INFO] 创建虚拟环境..."
    python3 -m venv venv
fi

echo "[INFO] 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "[INFO] 安装依赖..."
pip install -r requirements.txt -q 2>/dev/null || echo "[WARN] 部分依赖安装失败"

# 端口
PORT="${1:-8000}"

echo ""
echo "[INFO] 启动服务器: http://127.0.0.1:${PORT}"
echo "[INFO] API 文档: http://127.0.0.1:${PORT}/docs"
echo "[INFO] 按 Ctrl+C 停止"
echo ""

uvicorn app.main:app --host 127.0.0.1 --port "${PORT}" --reload
