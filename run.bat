@echo off
echo [RadioPartsDB] Starting launcher...

REM Check and activate virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo [Setup] Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [Setup] Installing dependencies...
    pip install fastapi uvicorn pydantic pyside6 >nul
)

REM Start Backend API if it exists
if exist backend\main.py (
    echo [Backend] Starting API server...
    start "RadioPartsDB-Backend" cmd /k python backend\main.py
    timeout /t 2 >nul
)

REM Start Desktop Application
echo [Desktop] Launching application...
python main.py

pause