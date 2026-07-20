@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PIP_DISABLE_PIP_VERSION_CHECK=1"

echo.
echo ========================================
echo   云游智导 - 灵山胜境本地交付版
echo ========================================
echo.

for %%F in ("requirements.txt" "tools\preflight.py" "tools\select_available_port.py" "app\main.py" "frontend-v4\index.html") do (
    if not exist %%F (
        echo [ERROR] 缺少 %%~F，请确认源码包完整。
        goto :failed
    )
)

set "BOOTSTRAP="
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 set "BOOTSTRAP=python"
if not defined BOOTSTRAP (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
    if not errorlevel 1 set "BOOTSTRAP=py -3"
)
if not defined BOOTSTRAP (
    echo [ERROR] 未找到 Python 3.11 或更高版本。
    echo [ERROR] 请安装 Python 3.11+，并确保 python 命令或 py 启动器可用。
    goto :failed
)

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] 首次运行，正在创建 .venv...
    %BOOTSTRAP% -m venv .venv || goto :failed
)

set "PYTHON=.venv\Scripts\python.exe"
"%PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 现有 .venv 不是可用的 Python 3.11+ 环境。
    echo [ERROR] 请删除项目根目录的 .venv 后重新运行本脚本。
    goto :failed
)

set "PORT=8000"
set "PORT_EXPLICIT=0"
if not "%~1"=="" set "PORT=%~1"
if not "%~1"=="" set "PORT_EXPLICIT=1"
"%PYTHON%" -c "import sys; p=sys.argv[1]; raise SystemExit(0 if p.isdigit() and 1 <= int(p) <= 65535 else 1)" "%PORT%" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 端口必须是 1 到 65535 之间的整数。
    goto :failed
)

set "PORT_FILE=.venv\.selected-port"
"%PYTHON%" tools\select_available_port.py "%PORT%" "%PORT_EXPLICIT%" "%PORT_FILE%" || goto :failed
set /p PORT=<"%PORT_FILE%"
del /q "%PORT_FILE%" >nul 2>&1
if not defined PORT (
    echo [ERROR] 无法确定服务端口。
    goto :failed
)

set "REQUIREMENTS_HASH="
set "CURRENT_HASH_FILE=.venv\.requirements.current.sha256"
"%PYTHON%" -c "import hashlib, pathlib; pathlib.Path(r'.venv/.requirements.current.sha256').write_text(hashlib.sha256(pathlib.Path('requirements.txt').read_bytes()).hexdigest(), encoding='ascii')" || goto :failed
set /p REQUIREMENTS_HASH=<"%CURRENT_HASH_FILE%"
del /q "%CURRENT_HASH_FILE%" >nul 2>&1
set "INSTALLED_HASH="
if exist ".venv\.requirements.sha256" set /p INSTALLED_HASH=<".venv\.requirements.sha256"

set "INSTALL_REQUIRED=0"
if not "%REQUIREMENTS_HASH%"=="%INSTALLED_HASH%" set "INSTALL_REQUIRED=1"
"%PYTHON%" -c "import certifi, edge_tts, fastapi, httpx, multipart, pydantic, pydantic_settings, pypdf, starlette, uvicorn" >nul 2>&1
if errorlevel 1 set "INSTALL_REQUIRED=1"
"%PYTHON%" -m pip check >nul 2>&1
if errorlevel 1 set "INSTALL_REQUIRED=1"

if "%INSTALL_REQUIRED%"=="1" (
    echo [INFO] 正在安装或更新项目依赖...
    "%PYTHON%" -m pip install -r requirements.txt || goto :failed
    "%PYTHON%" -m pip check || goto :failed
    "%PYTHON%" -c "import certifi, edge_tts, fastapi, httpx, multipart, pydantic, pydantic_settings, pypdf, starlette, uvicorn" >nul 2>&1 || goto :failed
    >".venv\.requirements.sha256" echo %REQUIREMENTS_HASH%
)

if not exist ".env" (
    echo [WARN] 未找到 .env，外部模型、语音和地图功能不会完整启用。
    echo [WARN] 可参考 .env.example 创建配置后重新启动。
)

echo [INFO] 正在执行启动前检查...
"%PYTHON%" tools\preflight.py || goto :failed

echo.
echo [INFO] 游客入口：http://127.0.0.1:%PORT%/
echo [INFO] 接口文档：http://127.0.0.1:%PORT%/docs
echo [INFO] 服务就绪后将自动打开浏览器。
echo [INFO] 按 Ctrl+C 停止服务。
echo.

if /i "%AUTO_OPEN_BROWSER%"=="0" goto :skip_browser_helper
start "" /b powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -Command "$healthUrl='http://127.0.0.1:%PORT%/health/live'; $targetUrl='http://127.0.0.1:%PORT%/'; $deadline=(Get-Date).AddSeconds(30); while ((Get-Date) -lt $deadline) { try { Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 1 | Out-Null; Start-Process $targetUrl; break } catch { Start-Sleep -Milliseconds 500 } }"
:skip_browser_helper

"%PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port "%PORT%" --workers 1
exit /b %errorlevel%

:failed
echo.
echo [ERROR] 启动准备失败，请根据上方信息修复后重试。
pause
exit /b 1
