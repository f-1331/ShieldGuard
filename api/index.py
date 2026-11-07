import os
import sys
from pathlib import Path

# Loyihaning asosiy ildiz papkasini Python yo'liga qo'shish
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Vercel serverless muhitini belgilash
os.environ["VERCEL"] = "1"

from backend.main import app
