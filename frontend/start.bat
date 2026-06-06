@echo off
cd /d "%~dp0"

echo LingJing TongXing - Starting...
echo.

if not exist "dist\index.html" (
    echo [Error] dist folder not found. Run: npm run build
    pause
    exit /b 1
)

python serve.py
