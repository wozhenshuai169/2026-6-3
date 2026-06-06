@echo off
REM ═══════════════════════════════════════════════════════
REM A5 智能导游系统 —— Windows 启动脚本
REM ═══════════════════════════════════════════════════════

echo.
echo ========================================
echo   A5 智能导游系统 v1.0.0
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv\Scripts\activate" (
    echo [INFO] 创建虚拟环境...
    python -m venv venv
)

echo [INFO] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo [INFO] 安装依赖...
pip install -r requirements.txt -q 2>&1
if %errorlevel% neq 0 (
    echo [WARN] 部分依赖安装失败，继续启动...
)

REM 检查 .env
if not exist ".env" (
    echo [WARN] .env 文件不存在，将使用默认配置
)

REM 端口
set PORT=8000
if not "%1"=="" set PORT=%1

echo.
echo [INFO] 启动服务器: http://127.0.0.1:%PORT%
echo [INFO] API 文档: http://127.0.0.1:%PORT%/docs
echo [INFO] 按 Ctrl+C 停止
echo.

uvicorn app.main:app --host 127.0.0.1 --port %PORT% --reload

pause
