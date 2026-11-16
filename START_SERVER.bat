@echo off
title ShieldGuard Pro AI - Unified Local Server & Render Failover Watchdog
cd /d "%~dp0"
echo ===================================================================
echo   ShieldGuard Pro AI - HA Bi-directional Failover Server (Port 8000)
echo ===================================================================
echo.
echo 1. Render Watchdog fonda ishga tushirilmoqda...
start "ShieldGuard Render Auto-Watchdog" /min python render_failback_watchdog.py
echo 2. Cloudflare Tunnel va Mahalliy Server ishga tushmoqda...
python run_unified_server.py
pause
