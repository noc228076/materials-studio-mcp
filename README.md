# Materials Studio MCP 服务

一个通过 BIOVIA MaterialsScript / MatServer 自动化 Materials Studio 的本地 MCP 服务。

本项目面向 Materials Studio 2020/20.1，正确入口是 `RunMatScript.bat`，不是
`MaterialsStudio.Application` COM。服务会自动探测本机 Materials Studio runner，MCP 配置里
通常不需要写 `env`。

## 1. 安装依赖

推荐使用项目内 `.venv`，这样 Claude Code 等客户端不会受系统 Python 环境影响。

```powershell
cd D:\APPS\AIMCP\materials-studio-mcp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

## 2. MCP 配置

推荐配置如下。不需要写 Materials Studio 路径，也不需要配置 `env`。

```json
{
  "type": "stdio",
  "command": "D:\\APPS\\AIMCP\\materials-studio-mcp\\.venv\\Scripts\\python.exe",
  "args": [
    "D:\\APPS\\AIMCP\\materials-studio-mcp\\run_server.py"
  ]
}
```

Claude Code 可用下面命令刷新用户级配置。

```powershell
claude mcp remove material_studio_mcp_server -s user
claude mcp add material_studio_mcp_server D:\APPS\AIMCP\materials-studio-mcp\.venv\Scripts\python.exe D:\APPS\AIMCP\materials-studio-mcp\run_server.py -s user
claude mcp list
```

看到 `material_studio_mcp_server ... ✓ Connected` 即表示连接成功。

## 3. 启动方式

MCP 客户端会自动启动服务。手动调试时可以运行：

```powershell
.\.venv\Scripts\python.exe .\run_server.py
```

也可以用启动脚本：

```powershell
.\start-material-studio-mcp.cmd
```

`start-material-studio-mcp.cmd` 会优先使用 `.venv`；如果 `.venv` 没装 `mcp`，会自动退回系统
Python。

## 4. Materials Studio 自动探测

服务启动后会自动查找 Materials Studio 2020/20.1 的 `RunMatScript.bat`。常见路径包括：

```text
D:\Program Files (x86)\BIOVIA\Materials Studio 20.1 x64 Server\etc\Scripting\bin\RunMatScript.bat
C:\Program Files\BIOVIA\Materials Studio 2020\etc\Scripting\bin\RunMatScript.bat
C:\Program Files (x86)\BIOVIA\Materials Studio 2020\etc\Scripting\bin\RunMatScript.bat
```

通常不需要手写环境变量。只有自动探测失败时，才需要设置：

```powershell
$env:MATERIAL_STUDIO_RUNNER = "D:\Program Files (x86)\BIOVIA\Materials Studio 20.1 x64 Server\etc\Scripting\bin\RunMatScript.bat"
```

## 5. 可用工具

- `material_studio_get_status`：检查服务和 Materials Studio runner 状态。
- `material_studio_build_tnt`：直接生成 2,4,6-三硝基甲苯 XSD，可选 Forcite 优化。
- `material_studio_build_molecule`：用 MaterialsScript `CreateAtom/CreateBond` 生成分子 XSD。
- `material_studio_run_script`：执行自定义 MaterialsScript Perl。
- `material_studio_validate_script`：检查 MaterialsScript 基本结构。
- `material_studio_import_export`：导入结构并导出为另一格式。
- `material_studio_structure_summary`：读取结构基础信息。
- `material_studio_forcite_geometry_optimization`：生成或执行 Forcite 几何优化。
- `material_studio_castep_energy_script`：生成 CASTEP Energy 脚本。
- `material_studio_list_script_templates`：列出内置脚本模板。

建模时优先使用 `material_studio_build_molecule` 或专用工具，不要手写 `.xsd` XML，也不要尝试
`MaterialsStudio.Application` COM。Server/MatServer 安装环境的正确入口是 MaterialsScript。

TNT 示例：

```json
{
  "output_file": "D:\\Documents\\AI\\zscq\\ppt\\TNT_ms_generated_optimized.xsd",
  "optimize": true,
  "timeout_seconds": 180
}
```

## 6. 验证

```powershell
claude mcp list
```

运行测试是开发检查，额外安装 `pytest` 后再执行：

```powershell
python -m pip install pytest
python -m pytest -q
```
