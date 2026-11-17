@echo off
title "ShieldGuard Pro AI - HA Server and Watchdog"
cd /d "%~dp0"

set PYTHON_BIN="C:\Users\hp\AppData\Local\Programs\Python\Python311\python.exe"
if not exist %PYTHON_BIN% set PYTHON_BIN=python

echo ===================================================================
echo   ShieldGuard Pro AI - HA Failover Server (Port 8080)
echo ===================================================================
echo.
echo 1. Render Watchdog fonda ishga tushirilmoqda...
start "ShieldGuard-Watchdog" /min %PYTHON_BIN% render_failback_watchdog.py
echo 2. Mahalliy Server va Tunnel ishga tushmoqda...
%PYTHON_BIN% run_unified_server.py
pause
