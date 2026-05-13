@echo off
chcp 65001 >nul
title Materials Studio MCP Server

setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%.venv"
set "PYTHON_CMD=python"

echo ============================================
echo   Materials Studio MCP Server - 一键启动
echo ============================================
echo.

:: ── 检查 Python ──────────────────────────────────
where %PYTHON_CMD% >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python 未找到，请安装 Python 3.10+
    pause
    exit /b 1
)

python -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 需要 Python 3.10 或更高版本
    pause
    exit /b 1
)
echo [OK] Python %PYTHON_CMD%

:: ── 虚拟环境 ──────────────────────────────────────
if exist "%VENV_DIR%\Scripts\python.exe" (
    set "PYTHON_CMD=%VENV_DIR%\Scripts\python.exe"
    echo [OK] 使用虚拟环境: %VENV_DIR%
) else (
    echo [INFO] 创建虚拟环境...
    python -m venv "%VENV_DIR%"
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] 创建虚拟环境失败
        pause
        exit /b 1
    )
    set "PYTHON_CMD=%VENV_DIR%\Scripts\python.exe"
    echo [OK] 虚拟环境已创建
)

:: ── 安装依赖 ──────────────────────────────────────
echo [INFO] 检查依赖...
"%PYTHON_CMD%" -m pip install --upgrade pip -q >nul 2>&1
"%PYTHON_CMD%" -m pip install -e "%PROJECT_DIR%" -q
if %ERRORLEVEL% neq 0 (
    echo [INFO] 安装依赖中...
    "%PYTHON_CMD%" -m pip install mcp numpy pywin32
    "%PYTHON_CMD%" -m pip install -e "%PROJECT_DIR%"
)
echo [OK] 依赖就绪

:: ── 菜单选择 ──────────────────────────────────────
echo.
echo 请选择启动模式:
echo   [1] stdio 模式 (默认，供 Claude Desktop 调用)
echo   [2] HTTP 模式 (可通过浏览器/API 测试)
echo   [3] 仅测试连接
echo.
set /p "MODE=输入选项 (1/2/3): "

echo.

if "%MODE%"=="2" (
    set /p "PORT=请输入端口号 (默认 8000): "
    if "!PORT!"=="" set "PORT=8000"
    echo [INFO] 启动 HTTP 模式，端口: !PORT!
    "%PYTHON_CMD%" -c "from materials_studio_mcp.server import mcp; mcp.run(host='127.0.0.1', port=!PORT!)"
    goto :end
)

if "%MODE%"=="3" (
    echo [INFO] 测试 Materials Studio 连接...
    "%PYTHON_CMD%" -c "
import sys, logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
from materials_studio_mcp.ms_client import MaterialsStudioClient
try:
    ms = MaterialsStudioClient(visible=True)
    ms.connect()
    print('[OK] Materials Studio 连接成功')
    print(f'     Version: {ms._app.Version}')
    ms.disconnect()
except Exception as e:
    print(f'[WARN] 连接失败: {e}')
    print('      服务器仍可启动，工具会提示手动连接')
"
    echo.
    pause
    goto :end
)

:: ── 默认: stdio 模式 ──────────────────────────────
echo [INFO] 启动 stdio 模式 (等待 Claude Desktop 调用)...
echo [INFO] 按 Ctrl+C 停止服务器
echo.
"%PYTHON_CMD%" -m materials_studio_mcp

:end
echo.
echo 服务器已停止
pause
