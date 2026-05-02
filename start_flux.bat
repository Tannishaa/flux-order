@echo off
echo ==========================================
echo    FLUX-ORDER MISSION CONTROL STARTUP
echo ==========================================
echo.
echo Waking up the system...

:: 1. Start the Python Worker (Handles the backend logic and Redis communication)
echo [1/3] Booting up the Worker node...
start "Flux Engine (Worker)" cmd /k "call venv\Scripts\activate.bat && python worker.py"

:: Give the worker a second to connect to Redis/AWS
timeout /t 2 /nobreak >nul

:: 2. Start the Terminal Dashboard (Monitors Redis and shows live order flow)
echo [2/3] Launching Mission Control Dashboard...
start "Flux Mission Control" cmd /k "call venv\Scripts\activate.bat && python monitor.py"

:: 3. Start the Next.js Frontend (Web Interface for users to place orders)
echo [3/3] Starting Next.js Web Interface...
start "Flux Web Interface" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================
echo ALL SYSTEMS STARTED
echo Close these black windows when you are done.
echo ==========================================
pause