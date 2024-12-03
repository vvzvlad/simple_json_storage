from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import json
import os
from pathlib import Path

app = FastAPI()

STORAGE_DIR = Path("storage")
MAX_TOTAL_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

# Создаем директорию для хранения, если её нет
STORAGE_DIR.mkdir(exist_ok=True)

def get_total_storage_size():
    """Подсчет общего размера всех файлов в хранилище"""
    total_size = 0
    for file_path in STORAGE_DIR.glob("*.json"):
        total_size += file_path.stat().st_size
    return total_size

def sanitize_path(path: str) -> str:
    """Очистка пути от потенциально опасных символов"""
    return "".join(c for c in path if c.isalnum() or c in "._-")

@app.put("/store/{path:path}")
async def store_json(path: str, request: Request):
    sanitized_path = sanitize_path(path)
    if not sanitized_path:
        raise HTTPException(status_code=400, detail="Invalid path")
    
    file_path = STORAGE_DIR / f"{sanitized_path}.json"
    
    try:
        json_data = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400, 
            detail="Invalid JSON data"
        )
    
    # Проверяем размер нового JSON
    json_str = json.dumps(json_data)
    new_file_size = len(json_str.encode('utf-8'))
    
    # Проверяем общий размер хранилища
    current_total_size = get_total_storage_size()
    
    # Если файл уже существует, не учитываем его размер в общем размере
    if file_path.exists():
        current_total_size -= file_path.stat().st_size
    
    # Проверяем, не превысит ли новый файл общий лимит
    if current_total_size + new_file_size > MAX_TOTAL_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Total storage limit exceeded. Current size: {current_total_size/1024/1024:.2f}MB, "
                   f"new file size: {new_file_size/1024/1024:.2f}MB, limit: 50MB"
        )
    
    # Сохраняем JSON
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f)
        return {
            "status": "success", 
            "path": sanitized_path,
            "storage_used_mb": (current_total_size + new_file_size) / 1024 / 1024
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

@app.get("/store/{path:path}")
async def get_json(path: str):
    sanitized_path = sanitize_path(path)
    file_path = STORAGE_DIR / f"{sanitized_path}.json"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return JSONResponse(json.load(f))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read file: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 