@echo off
title Materials Studio MCP Server
setlocal enabledelayedexpansion

set "DIR=%~dp0"
set "VENV=%DIR%.venv"
set "PY=python"

echo ============================================
echo   Materials Studio MCP Server
echo ============================================
echo.

where %PY% >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+
    pause
    exit /b 1
)

%PY% -c "import sys; exit(0 if sys.version_info>=(3,10) else 1)"
if errorlevel 1 (
    echo [ERROR] Need Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python ready

if exist "%VENV%\Scripts\python.exe" (
    set "PY=%VENV%\Scripts\python.exe"
    echo [OK] Using venv
) else (
    echo [..] Creating venv...
    "%PY%" -m venv "%VENV%"
    if errorlevel 1 (
        echo [ERROR] venv failed
        pause
        exit /b 1
    )
    set "PY=%VENV%\Scripts\python.exe"
    echo [OK] Venv ready
)

echo [..] Installing deps...
"%PY%" -m pip install -e "%DIR%" -q >nul 2>&1
if errorlevel 1 (
    "%PY%" -m pip install mcp numpy pywin32 >nul 2>&1
    "%PY%" -m pip install -e "%DIR%" >nul 2>&1
)
echo [OK] Dependencies ready

echo.
echo Select mode:
echo   [1] stdio (for Claude Desktop)
echo   [2] HTTP server
echo   [3] Test MS connection
echo.
set /p "MODE=Enter 1/2/3: "

if "%MODE%"=="2" (
    set /p "PORT=Enter port (8000): "
    if "!PORT!"=="" set "PORT=8000"
    echo [..] Starting HTTP on port !PORT!...
    "%PY%" -c "from materials_studio_mcp.server import mcp; mcp.run(host='127.0.0.1', port=!PORT!)"
    goto :END
)

if "%MODE%"=="3" (
    echo [..] Testing MS connection...
    "%PY%" -c "from materials_studio_mcp.ms_client import MaterialsStudioClient; ms=MaterialsStudioClient(visible=True); ms.connect(); print('[OK] MS connected, version: '+str(ms._app.Version)); ms.disconnect()"
    if errorlevel 1 (
        echo [WARN] MS not available. Server can still start with manual connect.
    )
    pause
    goto :END
)

echo [..] Starting stdio mode...
echo [..] Press Ctrl+C to stop
echo.
"%PY%" -m materials_studio_mcp

:END
echo.
pause
