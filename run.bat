@echo off
chcp 65001 >nul
echo ⏳ Запуск RadioPartsDB...
call venv\Scripts\activate.bat
python main.py
pause