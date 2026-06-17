@echo off
chcp 65001 >nul
setlocal
echo.
echo ========================================
echo   A5 Smart Guide System v1.0.0
echo ========================================
echo.

REM Go to script directory
cd /d "%~dp0"

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
pip install python-multipart -q 2>&1
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
echo [INFO] Starting backend server: http://127.0.0.1:%PORT%
echo [INFO] API docs:        http://127.0.0.1:%PORT%/docs
echo [INFO] Frontend v4:     http://127.0.0.1:%PORT%/
echo.

REM Start backend in a new visible window so errors can be seen
start "A5-Backend" cmd /k "cd /d %CD% && call venv\Scripts\activate.bat && uvicorn app.main:app --host 127.0.0.1 --port %PORT% --reload"

REM Wait for server to be ready (max 30 seconds)
echo [INFO] Waiting for server to be ready...
set /a count=0
:wait_loop
timeout /t 2 /nobreak >nul
curl -s http://127.0.0.1:%PORT%/ >nul 2>&1
if %errorlevel% equ 0 goto server_ready
set /a count+=2
if %count% geq 30 goto server_timeout
echo [INFO] Still waiting... (%count%s)
goto wait_loop

:server_timeout
echo.
echo [ERROR] Server failed to start within 30 seconds.
echo [INFO] Check the "A5-Backend" window for error messages.
echo.
pause
exit /b 1

:server_ready
echo [INFO] Server ready! Opening frontend v4...
start "" http://127.0.0.1:%PORT%/

echo.
echo ========================================
echo   Server running at http://127.0.0.1:%PORT%/
echo   Close "A5-Backend" window to stop.
echo ========================================
echo.

pause
endlocal
