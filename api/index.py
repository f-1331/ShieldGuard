import os
import sys
from pathlib import Path

# Add both current dir, parent dir, and /var/task to sys.path
for p in [
    str(Path(__file__).resolve().parent),
    str(Path(__file__).resolve().parent.parent),
    "/var/task"
]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["VERCEL"] = "1"

from backend.main import app
