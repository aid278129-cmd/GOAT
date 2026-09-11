@echo off
setlocal enabledelayedexpansion
title Zyntrix BIS Compliance Compiler

echo ==============================================================================
echo   ZYNTRIX BIS COMPLIANCE COMPILER — ONE-COMMAND STARTUP (WINDOWS)
echo   SIH Problem Statement 26107
echo ==============================================================================
echo.

REM 1. Validate Python Environment
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in PATH.
    echo Please install Python 3.10 or higher from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK] Detected Python %PY_VER%

REM 2. Validate Node.js Environment
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js/npm is not installed or not found in PATH.
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)
for /f "tokens=1" %%v in ('node -v 2^>^&1') do set NODE_VER=%%v
echo [OK] Detected Node.js %NODE_VER%

REM 3. Ensure .env exists
if not exist .env (
    echo [INFO] Creating .env from .env.example...
    copy .env.example .env >nul
)

REM 4. Ensure runtime directories exist
if not exist storage mkdir storage
if not exist uploads mkdir uploads
if not exist logs mkdir logs
if not exist generated mkdir generated
if not exist data mkdir data

REM 5. Install Dependencies if needed
if not exist backend\venv (
    if "%1"=="--install" (
        echo [INFO] Installing Python dependencies...
        python -m pip install -r requirements.txt
        echo [INFO] Installing frontend dependencies...
        cd frontend && call npm install && cd ..
    )
)

echo.
echo ==============================================================================
echo   LAUNCHING ZYNTRIX SERVICES
echo   Backend API:   http://localhost:8000
echo   API Docs:      http://localhost:8000/docs
echo   Health Check:  http://localhost:8000/api/v1/system/health
echo   Frontend UI:   http://localhost:5173
echo ==============================================================================
echo.

REM 6. Launch Backend in background console
start "Zyntrix Backend (FastAPI)" cmd /k "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"

REM 7. Launch Frontend in current window
echo Starting Frontend development server...
cd frontend
call npm run dev

pause
