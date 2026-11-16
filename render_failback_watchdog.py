import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s : %(message)s"
)
logger = logging.getLogger("ha_failover_watchdog")

BASE_DIR = Path(__file__).resolve().parent
RENDER_URL = "https://shieldguard-bot.onrender.com"
RENDER_HEALTH_URL = f"{RENDER_URL}/api/health"
LOCAL_HEALTH_URL = "http://127.0.0.1:8000/api/health"
OWNER_TELEGRAM_ID = 6707839718
TELEGRAM_BOT_TOKEN = "9237470345:AAFP4NeaViJGQOHPCGoMPvGZKkLY4lImtYI"
CHECK_INTERVAL_SECONDS = 90  # 90 soniyada bir marta tekshirish
STATE_FILE = BASE_DIR / "failover_state.json"


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "current_target": "UNKNOWN",
        "render_fail_count": 0,
        "render_success_count": 0,
        "last_switch_time": None
    }


def save_state(state: dict):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save state: {e}")


def get_current_vercel_target() -> str:
    vercel_path = BASE_DIR / "vercel.json"
    if not vercel_path.exists():
        return "UNKNOWN"
    try:
        with open(vercel_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "shieldguard-bot.onrender.com" in content:
            return "RENDER"
        elif "trycloudflare.com" in content:
            return "TUNNEL"
        elif "/api/index.py" in content:
            return "VERCEL_SERVERLESS"
    except Exception:
        pass
    return "UNKNOWN"


def get_active_tunnel_url() -> str:
    tunnel_file = BASE_DIR / "tunnel_url.txt"
    if tunnel_file.exists():
        try:
            with open(tunnel_file, "r", encoding="utf-8") as f:
                url = f.read().strip()
                if url.startswith("https://") and "trycloudflare.com" in url:
                    return url
        except Exception:
            pass
    return ""


def update_vercel_route(new_target_url: str, target_name: str) -> bool:
    vercel_path = BASE_DIR / "vercel.json"
    if not vercel_path.exists():
        logger.error("vercel.json topilmadi!")
        return False

    try:
        with open(vercel_path, "r", encoding="utf-8") as f:
            content = f.read()

        old_pattern = r'https://[a-zA-Z0-9\.\-]+\.(?:onrender\.com|trycloudflare\.com)'
        if re.search(old_pattern, content):
            new_content = re.sub(old_pattern, new_target_url, content)
        else:
            # Agar oldin /api/index.py bo'lgan bo'lsa
            new_content = content.replace(
                '"dest": "/api/index.py"',
                f'"dest": "{new_target_url}/api/$1"'
            )

        if new_content == content:
            logger.info(f"vercel.json allaqachon {new_target_url} manziliga yo'naltirilgan.")
            return True

        with open(vercel_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        logger.info(f"vercel.json yangilandi -> {new_target_url}")

        subprocess.run(["git", "add", "vercel.json"], cwd=str(BASE_DIR), check=True)
        subprocess.run(["git", "commit", "-m", f"chore(ha-failover): auto-route to {target_name} ({new_target_url})"], cwd=str(BASE_DIR), check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=str(BASE_DIR), check=True)
        logger.info(f"✅ Vercel yo'nalishi GitHub'ga muvaffaqiyatli push qilindi -> {target_name}")
        return True
    except Exception as e:
        logger.error(f"vercel.json yangilash yoki push qilishda xatolik: {e}")
        return False


def notify_owner_telegram(message_html: str):
    """Telegram bot orqali egasiga darhol ogohlantirish yuborish."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = json.dumps({
            "chat_id": OWNER_TELEGRAM_ID,
            "text": message_html,
            "parse_mode": "HTML"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                logger.info("✅ Telegram xabarnomasi muvaffaqiyatli yuborildi.")
    except Exception as e:
        logger.warning(f"Telegram orqali xabar yuborishda muammo: {e}")


def check_render_health() -> bool:
    """Render bulut serverining holatini tekshirish."""
    try:
        req = urllib.request.Request(RENDER_HEALTH_URL, headers={"User-Agent": "ShieldGuard-Watchdog/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status == 200:
                raw = resp.read().decode("utf-8", errors="ignore")
                try:
                    data = json.loads(raw)
                    if data.get("status") in ("healthy", "ok"):
                        return True
                except Exception:
                    pass
    except urllib.error.HTTPError as e:
        # 503 Service Suspended, 502, 500, 404
        logger.warning(f"Render HTTP javobi: {e.code} ({e.reason})")
    except Exception as e:
        logger.warning(f"Render ulanish xatosi: {e}")
    return False


def check_local_server_health() -> bool:
    """Lokal server holatini tekshirish."""
    try:
        req = urllib.request.Request(LOCAL_HEALTH_URL, headers={"User-Agent": "ShieldGuard-Watchdog/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


async def run_ha_watchdog():
    logger.info("=" * 65)
    logger.info("🔄 ShieldGuard Pro - Bi-directional HA Failover Watchdog")
    logger.info(f"   Primary Server:  Render ({RENDER_URL})")
    logger.info(f"   Backup Server:   Cloudflare Tunnel (Local Machine Port 8000)")
    logger.info(f"   Tekshiruv oralig'i: Har {CHECK_INTERVAL_SECONDS} soniyada")
    logger.info("=" * 65)

    state = load_state()

    while True:
        try:
            current_target = get_current_vercel_target()
            render_alive = check_render_health()

            if render_alive:
                state["render_success_count"] += 1
                state["render_fail_count"] = 0
                logger.info(f"[MONITOR] Render: ISHLAYAPTI (ketma-ket: {state['render_success_count']}) | Hozirgi Vercel nishoni: {current_target}")

                # 2-YO'NALISH (Render limiti yangilanganda va server tiklanganda):
                # Agar Vercel hozir TUNNEL'da bo'lsa va Render ketma-ket 2 marta 200 OK bersa -> FAILBACK
                if current_target == "TUNNEL" and state["render_success_count"] >= 2:
                    logger.info("🎉 RENDER BULUT SERVERI TIKLANDI! Failback boshlanmoqda...")
                    success = update_vercel_route(RENDER_URL, "RENDER")
                    if success:
                        state["current_target"] = "RENDER"
                        state["last_switch_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                        save_state(state)
                        msg = (
                            "🎉 <b>Render limiti yangilandi va server to'liq tiklandi!</b>\n\n"
                            "Vercel yo'nalishi avtomatik ravishda yana asosiy <b>Render bulut serveriga</b> (<code>shieldguard-bot.onrender.com</code>) qaytarildi.\n\n"
                            "✅ ShieldGuard AI kiber-himoya bot va sayti to'liq bulutda uzluksiz ishlamoqda!"
                        )
                        notify_owner_telegram(msg)
            else:
                state["render_fail_count"] += 1
                state["render_success_count"] = 0
                logger.warning(f"[MONITOR] Render: O'CHGAN/SUSPENDED (xatoliklar: {state['render_fail_count']}) | Hozirgi Vercel nishoni: {current_target}")

                # 1-YO'NALISH (Render limiti tugaganda / 503 Service Suspended):
                # Agar Render ketma-ket 2 marta ishlamasa va Vercel hali ham RENDER yoki VERCEL_SERVERLESS bo'lsa -> FAILOVER
                if current_target != "TUNNEL" and state["render_fail_count"] >= 2:
                    logger.warning("🚨 RENDER LIMITI TUGADI (503 Service Suspended)! Zaxira tunneliga almashtirilmoqda...")
                    tunnel_url = get_active_tunnel_url()
                    local_alive = check_local_server_health()

                    if tunnel_url and local_alive:
                        success = update_vercel_route(tunnel_url, "TUNNEL")
                        if success:
                            state["current_target"] = "TUNNEL"
                            state["last_switch_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                            save_state(state)
                            msg = (
                                "⚠️ <b>DIQQAT: Render oylik limiti tugadi (503 Service Suspended)!</b>\n\n"
                                "Tizim to'xtab qolmasligi uchun Vercel avtomatik ravishda <b>Zaxira (Cloudflare Tunnel)</b> kompyuter serveringizga ulandi.\n\n"
                                f"🌐 Jonli zaxira tunnel: <code>{tunnel_url}</code>\n"
                                "✅ ShieldGuard Pro Telegram bot va skanerlash 100% uzilishsiz ishlamoqda!"
                            )
                            notify_owner_telegram(msg)
                    else:
                        logger.error(f"Zaxira tunneliga ulanib bo'lmadi: local_alive={local_alive}, tunnel_url={tunnel_url}")

            save_state(state)

        except Exception as e:
            logger.error(f"Watchdog kutilmagan xatosi: {e}", exc_info=True)

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(run_ha_watchdog())
    except KeyboardInterrupt:
        logger.info("Watchdog to'xtatildi.")
