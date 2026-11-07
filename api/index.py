import os
import sys
from pathlib import Path

# Add possible root directories to sys.path
for p in [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parent.parent), "/var/task"]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["VERCEL"] = "1"

from backend.main import app as fastapi_app

try:
    from mangum import Mangum
    handler = Mangum(fastapi_app, lifespan="off")
    app = handler
except Exception:
    app = fastapi_app
