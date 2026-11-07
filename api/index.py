import os
import sys
from pathlib import Path

# Add search paths
root_dir = Path(__file__).resolve().parent.parent
for p in [str(root_dir), str(Path(__file__).resolve().parent), "/var/task"]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["VERCEL"] = "1"

from backend.main import app as _fastapi_app

# Top-level entrypoint for Vercel Python runtime
app = _fastapi_app
handler = _fastapi_app
