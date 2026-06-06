@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   A5 Smart Guide System v1.0.0
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Check venv
if not exist "venv\Scripts\activate" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

echo [INFO] Activating venv...
call venv\Scripts\activate.bat

REM Install deps
echo [INFO] Installing dependencies...
pip install -r requirements.txt -q 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Some dependencies failed to install, continuing...
)

REM Check .env
if not exist ".env" (
    echo [WARN] .env file not found, using default config
)

REM Port
set PORT=8000
if not "%1"=="" set PORT=%1

echo.
echo [INFO] Starting server: http://127.0.0.1:%PORT%
echo [INFO] API docs: http://127.0.0.1:%PORT%/docs
echo [INFO] Press Ctrl+C to stop
echo.

uvicorn app.main:app --host 127.0.0.1 --port %PORT% --reload

pause
