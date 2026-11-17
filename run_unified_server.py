import asyncio
import json
import logging
import os
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s : %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).resolve().parent / "unified_server.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("unified_server")

BASE_DIR = Path(__file__).resolve().parent
RENDER_URL = "https://shieldguard-bot.onrender.com"
RENDER_HEALTH_URL = f"{RENDER_URL}/api/health"


def find_free_port(preferred_ports=(8080, 8002, 8081, 8000)) -> int:
    """Kompyuterda ochiq va bo'sh portni avtomatik aniqlash."""
    for port in preferred_ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            res = s.connect_ex(("127.0.0.1", port))
            if res != 0:
                return port
    return 8080


SERVER_PORT = find_free_port()


def drain_tunnel_logs(proc):
    """Tunnel chiqargan loglarni fonda o'qib turish (pipe to'lib qolishini oldini oladi)."""
    log_file = BASE_DIR / "tunnel.log"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    break
                f.write(line)
                f.flush()
    except Exception:
        pass


def start_cloudflared_tunnel(port: int = SERVER_PORT):
    """Start cloudflared in the background and extract the live HTTPS tunnel URL."""
    cf_binary = BASE_DIR / "cloudflared.exe"
    if not cf_binary.exists():
        logger.error(f"cloudflared.exe not found at {cf_binary}")
        return None, None

    cmd = [str(cf_binary), "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"]
    logger.info(f"Starting Cloudflare Tunnel on http://127.0.0.1:{port} ...")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    tunnel_url = None
    start = time.time()
    while time.time() - start < 15:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        line_clean = line.strip()
        if "429" in line_clean or "failed with status 429" in line_clean:
            logger.warning("Cloudflare Tunnel rate limit (429) berdi!")
            proc.terminate()
            return None, None

        if "trycloudflare.com" in line_clean:
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line_clean)
            if match:
                tunnel_url = match.group(0)
                break

    if not tunnel_url:
        logger.warning("Failed to extract Cloudflare tunnel URL within 15 seconds.")
        proc.terminate()
        return None, None

    logger.info(f"✅ Live Cloudflare Tunnel URL: {tunnel_url}")
    with open(BASE_DIR / "tunnel_url.txt", "w", encoding="utf-8") as f:
        f.write(f"{tunnel_url}\n{port}")

    # Start background thread to drain pipe continuously
    threading.Thread(target=drain_tunnel_logs, args=(proc,), daemon=True).start()

    return proc, tunnel_url


def start_localtunnel(port: int = SERVER_PORT):
    """Localtunnel (npx localtunnel) orqali zaxira tunnel yaratish."""
    logger.info(f"Starting Localtunnel on port {port} ...")
    cmd = ["cmd.exe", "/c", "npx", "localtunnel", "--port", str(port)]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    tunnel_url = None
    start = time.time()
    while time.time() - start < 20:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        line_clean = line.strip()
        match = re.search(r"https://[a-zA-Z0-9-]+\.loca\.lt", line_clean)
        if match:
            tunnel_url = match.group(0)
            break

    if not tunnel_url:
        logger.warning("Localtunnel manzilini olish imkoni bo'lmadi.")
        proc.terminate()
        return None, None

    logger.info(f"✅ Live Localtunnel URL: {tunnel_url}")
    with open(BASE_DIR / "tunnel_url.txt", "w", encoding="utf-8") as f:
        f.write(f"{tunnel_url}\n{port}")

    threading.Thread(target=drain_tunnel_logs, args=(proc,), daemon=True).start()
    return proc, tunnel_url


def get_active_failover_tunnel(port: int = SERVER_PORT):
    """1-bosqich: Cloudflare, 2-bosqich: Localtunnel."""
    proc, url = start_cloudflared_tunnel(port)
    if url:
        return proc, url

    logger.info("Cloudflare ishlamadi, Localtunnel ishga tushirilmoqda...")
    proc, url = start_localtunnel(port)
    if url:
        return proc, url

    return None, None


def update_vercel_json_and_push(tunnel_url: str):
    """Update vercel.json routes to forward /api/(.*) to the active tunnel and git push."""
    vercel_path = BASE_DIR / "vercel.json"
    if not vercel_path.exists():
        logger.warning("vercel.json not found, skipping sync.")
        return

    try:
        with open(vercel_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Match any previous onrender.com, trycloudflare.com, or loca.lt target URL in /api/(.*)
        old_pattern = r'https://[a-zA-Z0-9\.\-]+\.(?:onrender\.com|trycloudflare\.com|loca\.lt)'
        if re.search(old_pattern, content):
            new_content = re.sub(old_pattern, tunnel_url, content)
        else:
            # If vercel.json was pointing to /api/index.py, switch /api/(.*) dest to tunnel
            new_content = content.replace(
                '"dest": "/api/index.py"',
                f'"dest": "{tunnel_url}/api/$1"'
            )

        if new_content != content:
            with open(vercel_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            logger.info(f"Updated vercel.json with live tunnel route -> {tunnel_url}")

            # Git commit and push
            subprocess.run(["git", "add", "vercel.json"], cwd=str(BASE_DIR), check=True)
            subprocess.run(["git", "commit", "-m", f"chore(tunnel): route API traffic to {tunnel_url}"], cwd=str(BASE_DIR), check=True)
            subprocess.run(["git", "push", "origin", "main"], cwd=str(BASE_DIR), check=True)
            logger.info("✅ Pushed new tunnel route to GitHub for instant Vercel sync!")
        else:
            logger.info("vercel.json is already up to date.")
    except Exception as e:
        logger.warning(f"Could not automatically sync vercel.json: {e}")


def is_render_suspended() -> bool:
    """Check if Render returns 503 or error."""
    import urllib.request
    try:
        req = urllib.request.Request(RENDER_HEALTH_URL, headers={"User-Agent": "ShieldGuard-Watchdog/1.0"})
        resp = urllib.request.urlopen(req, timeout=5)
        return resp.status != 200
    except urllib.error.HTTPError as e:
        if e.code in (503, 502, 500, 404):
            return True
    except Exception:
        return True
    return False


def main():
    logger.info("=" * 65)
    logger.info(f"🛡️ ShieldGuard Pro - Unified Server (Port: {SERVER_PORT})")
    logger.info("=" * 65)

    cf_proc, tunnel_url = get_active_failover_tunnel(SERVER_PORT)
    if tunnel_url:
        os.environ["BACKEND_URL"] = tunnel_url
        os.environ["RUN_LOCAL_POLLING"] = "0"

        # Agar Render limiti tugagan bo'lsa (503), darhol vercel.json ni tunnelga yo'naltirish
        render_suspended = is_render_suspended()
        if render_suspended:
            logger.warning("🚨 Render limiti tugagan (503)! Vercel zaxira tunneliga ulanmoqda...")
            update_vercel_json_and_push(tunnel_url)
        else:
            logger.info("Render bulut serveri faol holatda.")
    else:
        logger.warning("⚠️ Barcha tunnellar band! Telegram Bot to'g'ridan-to'g'ri lokal polling rejimida ishga tushiriladi...")
        os.environ["RUN_LOCAL_POLLING"] = "1"
        # Polling rejimida telegram webhookni tozalash kerak
        try:
            import urllib.request
            del_url = "https://api.telegram.org/bot9237470345:AAFP4NeaViJGQOHPCGoMPvGZKkLY4lImtYI/deleteWebhook?drop_pending_updates=False"
            urllib.request.urlopen(del_url, timeout=5)
            logger.info("Telegram webhook tozalandi (Long Polling faollashtirildi).")
        except Exception:
            pass

    # Write PID to file for tracking
    with open(BASE_DIR / "server.pid", "w") as f:
        f.write(str(os.getpid()))

    try:
        logger.info(f"🚀 Launching Uvicorn server on http://127.0.0.1:{SERVER_PORT} ...")
        from backend.main import app
        config = uvicorn.Config(app=app, host="0.0.0.0", port=SERVER_PORT, log_level="info", loop="asyncio")
        server = uvicorn.Server(config)
        server.run()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down unified server...")
    except Exception as e:
        logger.error(f"Uvicorn server unexpected error: {e}", exc_info=True)
    finally:
        if cf_proc and cf_proc.poll() is None:
            cf_proc.terminate()
            logger.info("Cloudflare tunnel terminated.")


if __name__ == "__main__":
    main()
