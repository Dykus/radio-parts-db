# backend/main.py
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Добавляем корень проекта в пути импорта, чтобы видеть core/
sys.path.append(str(Path(__file__).parent.parent))
from core.database import Database

# Пути (адаптируются под запуск из любой папки)
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "radioparts.db"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Выполняется при старте сервера"""
    if not DB_PATH.exists():
        print(f"⚠️ База данных не найдена по пути: {DB_PATH}")
    else:
        # Включаем WAL-режим для безопасной работы с несколькими подключениями
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.close()
    yield
    # Shutdown logic (если понадобится)

app = FastAPI(
    title="RadioPartsDB API",
    version="0.19.0",
    lifespan=lifespan
)

# Разрешаем браузеру делать запросы к этому серверу (для будущего фронтенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для локальной разработки. В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Зависимость: создаёт свежее подключение к БД на каждый запрос
def get_db():
    # check_same_thread=False критичен для FastAPI (многопоточность)
    db = Database(DB_PATH)
    try:
        yield db
    finally:
        # Если у вашего класса Database есть метод close() или cleanup(), вызовите его здесь
        pass 

@app.get("/")
def read_root():
    return {"status": "online", "message": "RadioPartsDB API v0.19.0"}

@app.get("/api/parts")
def get_parts(skip: int = 0, limit: int = 100, db: Database = Depends(get_db)):
    """Возвращает список деталей. Поддерживает пагинацию."""
    try:
        # Предполагается, что в вашей Database есть метод get_all_parts_filtered()
        # Если он требует аргументы, передайте None по умолчанию
        parts = db.get_all_parts_filtered(category_id=None, filter_type="all", location_path=None)
        return parts[skip:skip+limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print(f" Запуск сервера на http://0.0.0.0:8000")
    print(f"📖 Swagger Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)