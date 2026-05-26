@echo off
chcp 65001 >nul
echo ==========================================
echo    RadioPartsDB - Auto Launcher
echo ==========================================

REM 1. Переходим в папку проекта
cd /d "%~dp0"

REM 2. Создаем виртуальное окружение, если его нет
if not exist "venv\Scripts\python.exe" (
    echo [INFO] Виртуальное окружение не найдено. Создаю...
    python -m venv venv
)

REM 3. Устанавливаем/обновляем все нужные библиотеки из requirements.txt
echo [INFO] Проверка зависимостей (это может занять минуту)...
venv\Scripts\python.exe -m pip install -q -r requirements.txt

REM 4. Запускаем Backend API в отдельном окне
echo [INFO] Запуск Backend API...
start "RadioPartsDB-Backend" cmd /k "venv\Scripts\python.exe backend\main.py"

REM Пауза 3 секунды, чтобы сервер успел стартовать
timeout /t 3 >nul

REM 5. Запускаем Desktop приложение в отдельном окне
echo [INFO] Запуск Desktop приложения...
start "RadioPartsDB-Desktop" cmd /k "venv\Scripts\python.exe main.py"

REM 6. Открываем Web-интерфейс в браузере
echo [INFO] Открытие Web-клиента...
if exist "frontend\index.html" (
    start "" "%CD%\frontend\index.html"
)

echo.
echo ✅ Все компоненты запущены!
echo    • Backend: http://localhost:8000/docs
echo    • Desktop: отдельное окно
echo    • Web: открыт в браузере
echo.
pause