from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from pathlib import Path
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STORAGE_DIR = Path("storage")
MAX_TOTAL_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB

# Create storage directory if it doesn't exist
STORAGE_DIR.mkdir(exist_ok=True)

def get_total_storage_size():
    """Calculate total size of all files in storage"""
    total_size = 0
    for file_path in STORAGE_DIR.glob("*.json"):
        total_size += file_path.stat().st_size
    return total_size

def sanitize_path(path: str) -> str:
    """Clean path from potentially dangerous characters"""
    return "".join(c for c in path if c.isalnum() or c in "._-")

@app.put("/store/{path:path}")
async def store_json(path: str, request: Request):
    sanitized_path = sanitize_path(path)
    if not sanitized_path:
        logger.warning(f"Invalid path attempted: {path}")
        raise HTTPException(status_code=400, detail="Invalid path")
    
    file_path = STORAGE_DIR / f"{sanitized_path}.json"
    logger.info(f"Attempting to store JSON at path: {sanitized_path}")
    
    try:
        json_data = await request.json()
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON data received: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail="Invalid JSON data"
        )
    
    json_str = json.dumps(json_data)
    new_file_size = len(json_str.encode('utf-8'))
    current_total_size = get_total_storage_size()
    
    if file_path.exists():
        current_total_size -= file_path.stat().st_size
        logger.info(f"Updating existing file: {sanitized_path}, current size: {file_path.stat().st_size/1024:.2f}KB")
    
    if current_total_size + new_file_size > MAX_TOTAL_SIZE_BYTES:
        logger.warning(
            f"Storage limit exceeded - Current: {current_total_size/1024/1024:.2f}MB, "
            f"New: {new_file_size/1024/1024:.2f}MB, Limit: 50MB"
        )
        raise HTTPException(
            status_code=413,
            detail=f"Total storage limit exceeded. Current size: {current_total_size/1024/1024:.2f}MB, "
                   f"new file size: {new_file_size/1024/1024:.2f}MB, limit: 50MB"
        )
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f)
        logger.info(
            f"Successfully stored JSON at {sanitized_path}. "
            f"File size: {new_file_size/1024:.2f}KB, "
            f"Total storage used: {(current_total_size + new_file_size)/1024/1024:.2f}MB"
        )
        return {
            "status": "success", 
            "path": sanitized_path,
            "storage_used_mb": (current_total_size + new_file_size) / 1024 / 1024
        }
    except Exception as e:
        logger.error(f"Failed to save file {sanitized_path}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

@app.get("/store/{path:path}")
async def get_json(path: str):
    sanitized_path = sanitize_path(path)
    file_path = STORAGE_DIR / f"{sanitized_path}.json"
    logger.info(f"Attempting to read JSON from path: {sanitized_path}")
    
    if not file_path.exists():
        logger.warning(f"File not found: {sanitized_path}")
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Successfully read JSON from {sanitized_path}")
            return JSONResponse(data)
    except Exception as e:
        logger.error(f"Failed to read file {sanitized_path}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read file: {str(e)}"
        )

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Simple JSON Storage</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 40px auto;
                    padding: 0 20px;
                    line-height: 1.6;
                }
                code {
                    background: #f4f4f4;
                    padding: 2px 5px;
                    border-radius: 3px;
                }
            </style>
        </head>
        <body>
            <h1>Simple JSON Storage</h1>
            <p>This is a simple JSON storage service with the following endpoints:</p>
            <ul>
                <li><code>PUT /store/{path}</code> - Store JSON data</li>
                <li><code>GET /store/{path}</code> - Retrieve JSON data</li>
            </ul>
            <p>Maximum total storage size: 50MB</p>
            <h2>Example Usage:</h2>
            <pre>
# Store data
curl -X PUT http://localhost:8000/store/my/data -H "Content-Type: application/json" -d '{"key": "value"}'

# Retrieve data
curl http://localhost:8000/store/my/data
            </pre>
        </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 