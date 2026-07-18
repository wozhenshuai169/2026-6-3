@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ========================================
echo   云游智导 - 灵山胜境本地交付版
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到 Python，请安装 Python 3.10 或更高版本。
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] 首次运行，正在创建 .venv...
    python -m venv .venv || goto :failed
)

set "PYTHON=.venv\Scripts\python.exe"
"%PYTHON%" -c "import fastapi, uvicorn, httpx, edge_tts" >nul 2>&1
if errorlevel 1 (
    echo [INFO] 首次运行，正在安装依赖...
    "%PYTHON%" -m pip install -r requirements.txt || goto :failed
)

if not exist ".env" (
    echo [WARN] 未找到 .env，外部模型和地图功能将按配置降级。
    echo [WARN] 可参考 .env.example 创建配置后重新启动。
)

echo [INFO] 正在执行启动前检查...
"%PYTHON%" tools\preflight.py || goto :failed

set "PORT=8000"
if not "%~1"=="" set "PORT=%~1"

echo.
echo [INFO] 游客入口：http://127.0.0.1:%PORT%/
echo [INFO] 接口文档：http://127.0.0.1:%PORT%/docs
echo [INFO] 按 Ctrl+C 停止服务。
echo.
"%PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port %PORT% --workers 1
exit /b %errorlevel%

:failed
echo.
echo [ERROR] 启动准备失败，请根据上方信息修复后重试。
pause
exit /b 1
