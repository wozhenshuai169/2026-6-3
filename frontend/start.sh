#!/bin/bash
set -e
cd "$(dirname "$0")"

# 如果没有 dist 目录，先构建
if [ ! -d "dist" ]; then
    echo "[1/2] 正在构建前端项目..."
    npm run build
    echo ""
fi

echo "[2/2] 启动服务并打开浏览器..."
echo ""

# 用 Python 启动服务（自动打开浏览器）
if command -v python3 &> /dev/null; then
    python3 serve.py
elif command -v python &> /dev/null; then
    python serve.py
elif command -v npx &> /dev/null; then
    open http://localhost:8080 2>/dev/null || xdg-open http://localhost:8080 2>/dev/null &
    npx serve dist -p 8080 --no-clipboard
else
    echo "[错误] 未找到 Python 或 Node.js"
    exit 1
fi
