import uvicorn
import os
import sys

# Windows terminallarida UTF-8 qo'llab-quvvatlash
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Loyihaning ildiz papkasini sys.path ga qo'shish
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.config import settings

if __name__ == "__main__":
    print(f"==================================================")
    print(f"🛡️  SHIELDGUARD AI — KIBER-XAVFSIZLIK VA YURIDIK QALQON")
    print(f"==================================================")
    print(f"🚀 Server manzili: http://{settings.HOST}:{settings.PORT}")
    print(f"📱 WebApp manzili: http://localhost:{settings.PORT}/webapp")
    print(f"🤖 Telegram Bot  : @{settings.TELEGRAM_BOT_USERNAME}")
    print(f"==================================================")
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False
    )
