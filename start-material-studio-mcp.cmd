@echo off
setlocal
set SCRIPT_DIR=%~dp0
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
  "%SCRIPT_DIR%.venv\Scripts\python.exe" -c "import mcp" >nul 2>nul
  if not errorlevel 1 (
    "%SCRIPT_DIR%.venv\Scripts\python.exe" "%SCRIPT_DIR%run_server.py"
    exit /b %ERRORLEVEL%
  )
)
python "%SCRIPT_DIR%run_server.py"
exit /b %ERRORLEVEL%
