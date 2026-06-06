@echo off
chcp 65001 >nul
echo ========================================
echo   Lingjing Tongxing - AI Digital Human
echo ========================================
echo.
echo Installing dependencies...
call npm install
echo.
echo Starting dev server...
echo   Visitor : http://localhost:5173
echo   Guide   : http://localhost:5173/guide
echo   Admin   : http://localhost:5173/admin
echo.
npm run dev
pause
