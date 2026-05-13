param(
    [ValidateSet("stdio", "http", "test")]
    [string]$Mode = "stdio",
    [int]$Port = 8000
)

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ProjectDir ".venv"
$PythonCmd = "python"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Materials Studio MCP Server - 一键启动" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ── Check Python ──────────────────────────────────
try {
    $ver = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    if ([version]$ver -lt [version]"3.10") { throw "Python 3.10+ required, got $ver" }
    Write-Host "[OK] Python $ver" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python 3.10+ 未找到: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# ── Virtual Environment ───────────────────────────
$venvPython = Join-Path $VenvDir "Scripts\python.exe"
if (Test-Path $venvPython) {
    $PythonCmd = $venvPython
    Write-Host "[OK] 使用虚拟环境: $VenvDir" -ForegroundColor Green
} else {
    Write-Host "[INFO] 创建虚拟环境..." -ForegroundColor Yellow
    python -m venv $VenvDir
    $PythonCmd = $venvPython
    Write-Host "[OK] 虚拟环境已创建" -ForegroundColor Green
}

# ── Install Dependencies ─────────────────────────
Write-Host "[INFO] 检查依赖..." -ForegroundColor Yellow
& $PythonCmd -m pip install --upgrade pip -q 2>$null
& $PythonCmd -m pip install -e $ProjectDir -q 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[INFO] 安装依赖中..." -ForegroundColor Yellow
    & $PythonCmd -m pip install mcp numpy pywin32 2>&1 | Out-Null
    & $PythonCmd -m pip install -e $ProjectDir 2>&1 | Out-Null
}
Write-Host "[OK] 依赖就绪" -ForegroundColor Green

# ── Mode Selection ───────────────────────────────
if ($Mode -eq "http") {
    Write-Host "[INFO] 启动 HTTP 模式，端口: $Port" -ForegroundColor Yellow
    & $PythonCmd -c "from materials_studio_mcp.server import mcp; mcp.run(host='127.0.0.1', port=$Port)"
    return
}

if ($Mode -eq "test") {
    Write-Host "[INFO] 测试 Materials Studio 连接..." -ForegroundColor Yellow
    try {
        $script = @"
import sys, logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
from materials_studio_mcp.ms_client import MaterialsStudioClient
ms = MaterialsStudioClient(visible=True)
ms.connect()
print(f'Version: {ms._app.Version}')
ms.disconnect()
"@
        & $PythonCmd -c $script
        Write-Host "[OK] Materials Studio 连接成功" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] 连接失败: $_" -ForegroundColor Yellow
        Write-Host "       服务器仍可启动，工具会提示手动连接" -ForegroundColor Yellow
    }
    Read-Host "Press Enter to exit"
    return
}

# ── Default: stdio mode ──────────────────────────
Write-Host "[INFO] 启动 stdio 模式 (等待 Claude Desktop 调用)..." -ForegroundColor Yellow
Write-Host "[INFO] 按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host ""
& $PythonCmd -m materials_studio_mcp

Write-Host ""
Write-Host "服务器已停止" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
