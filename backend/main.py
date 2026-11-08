import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings, BASE_DIR
from backend.database import init_db
from backend.routers import scan, family, community, history, admin, tools
from backend.telegram_bot import start_telegram_bot

# Log sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ShieldGuard")

bot_task: asyncio.Task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Baza jadvallarini ishga tushirish
    logger.info("Ma'lumotlar bazasi initsializatsiya qilinmoqda...")
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Ma'lumotlar bazasini ishga tushirishda xatolik: {e}")

    # 2. Telegram botni fonga qo'yish (Faqat RUN_LOCAL_POLLING=1 bo'lgandagina lokal polling)
    global bot_task
    run_polling = os.environ.get("RUN_LOCAL_POLLING") == "1"
    if run_polling and settings.TELEGRAM_BOT_TOKEN and "your_bot_token" not in settings.TELEGRAM_BOT_TOKEN:
        logger.info("ShieldGuard Telegram Bot lokal fonga ulanmoqda (Polling)...")
        bot_task = asyncio.create_task(start_telegram_bot())
    else:
        # Vercel / Cloud Serverless rejimi (Doimiy Webhook himoyasi)
        logger.info("ShieldGuard Webhook rejimi faol. Webhook holati tekshirilmoqda...")
        try:
            from backend.telegram_bot import bot
            target_webhook = f"{settings.WEBAPP_URL}/api/webhook"
            wh_info = await bot.get_webhook_info()
            if wh_info.url != target_webhook:
                logger.info(f"Telegram Webhook tiklanmoqda -> {target_webhook}")
                await bot.set_webhook(url=target_webhook, drop_pending_updates=False)
        except Exception as e:
            logger.warning(f"Webhookni avtomatik tekshirishda ogohlantirish: {e}")

    yield

    # O'chirish (Shutdown)
    if bot_task:
        logger.info("Telegram Bot foni to'xtatilmoqda...")
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Kiber-xavfsizlik, fishing filtri, APK troyan tahlili va yuridik shartnomalar rentgeni (O'zbek tilida)",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routerlarni ulash
app.include_router(scan.router)
app.include_router(family.router)
app.include_router(community.router)
app.include_router(history.router)
app.include_router(admin.router)
app.include_router(tools.router)

# Frontend statik fayllarini ulash
FRONTEND_DIR = BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/", response_class=FileResponse)
async def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>ShieldGuard AI</h1><p>Frontend yuklanmadi.</p>")

@app.get("/webapp", response_class=FileResponse)
async def serve_webapp():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>ShieldGuard Mini App</h1>")

@app.get("/api/health")
async def health_check():
    webhook_status = "unknown"
    try:
        from backend.telegram_bot import bot
        wh = await bot.get_webhook_info()
        webhook_status = wh.url or "disconnected"
        # Self-healing: Agar webhook uzilib qolgan bo'lsa, zudlik bilan qayta tiklash
        target_wh = f"{settings.WEBAPP_URL}/api/webhook"
        if not wh.url and settings.TELEGRAM_BOT_TOKEN:
            await bot.set_webhook(url=target_wh, drop_pending_updates=False)
            webhook_status = f"{target_wh} (auto-recovered)"
    except Exception as e:
        webhook_status = f"error: {e}"

    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "is_vercel": bool(os.environ.get("VERCEL")),
        "telegram_webhook": webhook_status,
        "bot_active": True
    }

# ==========================================
# Telegram Webhook (Vercel & Cloud Hosting)
# ==========================================

@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    """Vercel / Cloud serverless uchun Telegram Webhook qabul qiluvchisi."""
    try:
        update_data = await request.json()
        from aiogram.types import Update
        from backend.telegram_bot import bot, dp
        update = Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Webhook xatoligi: {e}")
        return {"ok": False, "error": str(e)}

@app.get("/api/set-webhook")
async def set_telegram_webhook(url: str = None):
    """Telegram Webhook manzilini ulash."""
    from backend.telegram_bot import bot
    target_url = url or f"{settings.WEBAPP_URL}/api/webhook"
    try:
        res = await bot.set_webhook(url=target_url, drop_pending_updates=False)
        return {
            "status": "success",
            "message": f"Webhook muvaffaqiyatli ulandi: {target_url}",
            "telegram_response": res
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/delete-webhook")
async def delete_telegram_webhook():
    """Telegram Webhookni bekor qilish (Mahalliy polling rejimiga qaytarish)."""
    from backend.telegram_bot import bot
    try:
        res = await bot.delete_webhook(drop_pending_updates=False)
        return {
            "status": "success",
            "message": "Webhook o'chirildi! Endi mahalliy kompyuterdan polling ishlashi mumkin.",
            "telegram_response": res
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/webhook-info")
async def get_telegram_webhook_info():
    """Telegram webhook holatini tekshirish."""
    from backend.telegram_bot import bot
    try:
        info = await bot.get_webhook_info()
        return {"status": "success", "info": info.model_dump()}
    except Exception as e:
        return {"status": "error", "message": str(e)}
