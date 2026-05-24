@echo off
echo [RadioPartsDB] Starting...

REM Check venv
if not exist "venv\Scripts\python.exe" (
    echo ERROR: venv not found
    pause
    exit /b
)

REM Start Backend in new window
start "Backend" cmd /k "venv\Scripts\python.exe backend\main.py"

REM Wait for server
timeout /t 3 >nul

REM Start Desktop
start "Desktop" cmd /k "venv\Scripts\python.exe main.py"

REM Open Web
if exist "frontend\index.html" (
    start "" "%CD%\frontend\index.html"
)

echo All components launched.
pause