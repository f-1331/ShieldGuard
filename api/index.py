import os
import sys
import traceback
from pathlib import Path

# Add all possible source locations to sys.path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent

for p in [str(current_dir), str(parent_dir), "/var/task"]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["VERCEL"] = "1"

try:
    from backend.main import app
except Exception as e:
    tb = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    app = FastAPI()
    
    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
    async def catch_all_error(path: str = ""):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Startup error in Vercel serverless function",
                "details": str(e),
                "traceback": tb,
                "sys_path": sys.path
            }
        )
