import asyncio
import json
import logging
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s : %(message)s"
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
    while time.time() - start < 35:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        line_clean = line.strip()
        if "trycloudflare.com" in line_clean:
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line_clean)
            if match:
                tunnel_url = match.group(0)
                break

    if not tunnel_url:
        logger.error("Failed to extract tunnel URL within 35 seconds.")
        proc.terminate()
        return None, None

    logger.info(f"✅ Live Cloudflare Tunnel URL: {tunnel_url}")
    with open(BASE_DIR / "tunnel_url.txt", "w", encoding="utf-8") as f:
        f.write(f"{tunnel_url}\n{port}")

    return proc, tunnel_url


def update_vercel_json_and_push(tunnel_url: str):
    """Update vercel.json routes to forward /api/(.*) to the active tunnel and git push."""
    vercel_path = BASE_DIR / "vercel.json"
    if not vercel_path.exists():
        logger.warning("vercel.json not found, skipping sync.")
        return

    try:
        with open(vercel_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Match any previous onrender.com or trycloudflare.com target URL in /api/(.*)
        old_pattern = r'https://[a-zA-Z0-9\.\-]+\.(?:onrender\.com|trycloudflare\.com)'
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

    cf_proc, tunnel_url = start_cloudflared_tunnel(SERVER_PORT)
    if not tunnel_url:
        logger.error("Cannot proceed without an active Cloudflare tunnel.")
        sys.exit(1)

    os.environ["BACKEND_URL"] = tunnel_url
    os.environ["RUN_LOCAL_POLLING"] = "0"

    # Agar Render limiti tugagan bo'lsa (503), darhol vercel.json ni tunnelga yo'naltirish
    render_suspended = is_render_suspended()
    if render_suspended:
        logger.warning("🚨 Render limiti tugagan (503)! Vercel zaxira tunneliga ulanmoqda...")
        update_vercel_json_and_push(tunnel_url)
    else:
        logger.info("Render bulut serveri faol holatda.")

    try:
        logger.info(f"🚀 Launching Uvicorn server on http://127.0.0.1:{SERVER_PORT} ...")
        from backend.main import app
        uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT, log_level="info")
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down unified server...")
    finally:
        if cf_proc and cf_proc.poll() is None:
            cf_proc.terminate()
            logger.info("Cloudflare tunnel terminated.")


if __name__ == "__main__":
    main()
