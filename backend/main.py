# backend/main.py
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
import uvicorn

sys.path.append(str(Path(__file__).parent.parent))
from core.database import Database

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "radioparts.db"

# === Pydantic модели ===

class PartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    part_type: Optional[str] = None
    package: Optional[str] = None
    quantity: int = 0
    price: float = 0.0
    location: Optional[str] = None
    status: str = "Новое"
    category_id: Optional[int] = None
    image_path: Optional[str] = None
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    mpn: Optional[str] = None

class PartCreate(BaseModel):
    name: str
    part_type: Optional[str] = None
    package: Optional[str] = None
    quantity: int = 0
    price: float = 0.0
    location: Optional[str] = None
    status: str = "Новое"
    category_id: Optional[int] = None
    image_path: Optional[str] = None
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    mpn: Optional[str] = None

class PartUpdate(BaseModel):
    name: Optional[str] = None
    part_type: Optional[str] = None
    package: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[float] = None
    location: Optional[str] = None
    status: Optional[str] = None
    category_id: Optional[int] = None
    image_path: Optional[str] = None
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    mpn: Optional[str] = None

# === Инициализация ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    if not DB_PATH.exists():
        print(f"⚠️ База данных не найдена: {DB_PATH}")
    else:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.close()
        print(f"✅ База данных подключена: {DB_PATH}")
    yield

app = FastAPI(title="RadioPartsDB API", version="0.19.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = Database(DB_PATH)
    try: yield db
    finally: pass

# === Helpers ===

def _patch_db_dict(d: dict) -> dict:
    """Добавляет отсутствующие ключи со значением None для совместимости с Pydantic V2"""
    required = ['part_type', 'package', 'location', 'category_id', 'image_path', 
                'description', 'manufacturer', 'mpn', 'status']
    for key in required:
        if key not in d:
            d[key] = None
    if not d.get('status'):
        d['status'] = "Новое"
    return d

# === Endpoints ===

@app.get("/")
def read_root():
    return {"status": "online", "message": "RadioPartsDB API v0.19.0"}

@app.get("/api/parts", response_model=List[PartResponse])
def get_parts(skip: int = 0, limit: int = 100, db: Database = Depends(get_db)):
    try:
        parts = db.get_all_parts_filtered(category_id=None, filter_type="all", location_path=None)
        # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: патчим словари перед валидацией
        fixed = [_patch_db_dict(p.copy()) for p in parts]
        return fixed[skip:skip+limit]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/parts/{part_id}", response_model=PartResponse)
def get_part(part_id: int, db: Database = Depends(get_db)):
    part = db.get_part(part_id)
    if not part: raise HTTPException(status_code=404, detail="Part not found")
    return _patch_db_dict(part.copy())

@app.post("/api/parts", response_model=PartResponse)
def create_part(part: PartCreate, db: Database = Depends(get_db)):
    try:
        new_id = db.create_part(part.model_dump())
        return _patch_db_dict(db.get_part(new_id).copy())
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/parts/{part_id}", response_model=PartResponse)
def update_part(part_id: int, part: PartUpdate, db: Database = Depends(get_db)):
    try:
        existing = db.get_part(part_id)
        if not existing: raise HTTPException(status_code=404, detail="Part not found")
        update_data = {k: v for k, v in part.model_dump().items() if v is not None}
        db.update_part(part_id, {**existing, **update_data})
        return _patch_db_dict(db.get_part(part_id).copy())
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/parts/{part_id}")
def delete_part(part_id: int, db: Database = Depends(get_db)):
    try:
        db.delete_part(part_id)
        return {"message": "Part deleted"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories")
def get_categories(db: Database = Depends(get_db)):
    return db.get_categories()

@app.get("/api/categories/tree")
def get_categories_tree(db: Database = Depends(get_db)):
    cats = db.get_categories()
    tree, item_map = {}, {}
    for cid, name, pid in cats: item_map[cid] = {"name": name, "children": {}}
    for cid, name, pid in cats:
        if pid in (None, 0) or pid not in item_map: tree[name] = item_map[cid]["children"]
        else: item_map[pid]["children"][name] = item_map[cid]["children"]
    return tree

@app.get("/api/locations/tree")
def get_locations_tree(db: Database = Depends(get_db)):
    return db.get_location_tree()

@app.get("/api/stats")
def get_stats(db: Database = Depends(get_db)):
    return db.get_stats()

if __name__ == "__main__":
    print("🚀 Starting server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)