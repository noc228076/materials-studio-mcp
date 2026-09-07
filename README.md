# Materials Studio MCP 服务 (materials-studio-mcp)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Spec](https://img.shields.io/badge/MCP-2024--11--05-brightgreen.svg)](https://modelcontextprotocol.io/)
[![Materials Studio](https://img.shields.io/badge/Materials%20Studio-2020%20%7C%2020.1-orange.svg)](https://www.3ds.com/products-services/biovia/products/molecular-modeling-simulation/biovia-materials-studio/)
[![Tests Passed](https://img.shields.io/badge/tests-31%20passed-success.svg)](tests/)

专为材料科学、计算化学与凝聚态物理研究打造的本地 **Model Context Protocol (MCP)** 服务。

通过本服务，**Claude、Cursor、ChatGPT、DeepSeek** 等大语言模型可直接驱动底层商业级分子建模与模拟软件 **BIOVIA Materials Studio**，实现自动化材料建模、官方结构库检索、周期性晶体/超胞/表面切片构建、Forcite 几何优化与分子动力学、CASTEP 第一性原理 DFT 计算与 Reflex XRD 粉末衍射图谱模拟全流程贯通。

---

## 1. 为什么选择 MaterialsScript 方案？（技术原理与避坑）

在尝试让 AI 自动化操作 Materials Studio 时，常见的技术误区包括：
1. **误区一：手写 `.xsd` XML 文件**
   Materials Studio 的 `.xsd` 格式内部包含复杂的层级拓扑、视图投影与专有二进制哈希校验，手写极易损坏，导致软件崩溃报错。
2. **误区二：调用 `MaterialsStudio.Application` (Windows OLE/COM)**
   Materials Studio 官方的 COM 组件严重依赖前台图形界面，在 Windows 64 位服务器环境（Server / MatServer 安装版）中未正确注册，无法脱机/无头（Headless）运行，极易出现句柄泄露与窗口死锁。

### 本项目的技术路线：
本项目严格遵循 BIOVIA 官方的最佳实践——**基于 `RunMatScript.bat` 的 MaterialsScript 原生引擎**：
- **官方 API 级建模**：通过 MaterialsScript 原生 `CreateAtom`、`CreateBond`、`Lattice3D`、`DefineCleave` 等接口构建模型，由 MS 内核负责导出标准 `.xsd`，格式 100% 合规。
- **完全无头（Headless）执行**：后台独立工作区调度，不弹出前台 GUI，不干扰用户正常桌面操作。
- **真正的多核并行**：全面支持 `-np <cores>` 分布式/多核并行加速，彻底告别单核慢速运算。
- **Dry-run 安全机制**：所有工具均支持 `dry_run=true`，可只生成 Perl 脚本进行前置语法审查，无需消耗算力或许可证。

---

## 2. 核心支持功能与模块

- **结构探索**：支持 Materials Studio 官方 `share/Structures` 数千种晶体结构库（半导体、金属、沸石、催化剂等）的模糊搜索与一键载入。
- **分子拓扑**：内置标准分子模板库（水、甲烷、苯、TNT、乙醇等），支持自定义原子与键拓扑快速建模。
- **晶体与表面**：支持根据晶胞常数（$a, b, c, \alpha, \beta, \gamma$）、分数坐标与空间群构建晶体，支持超胞展开（$u, v, w$）及表面晶面切片（$h, k, l$）与真空层构建。
- **分子力学与动力学 (Forcite)**：支持 COMPASS/Universal 等力场的几何优化，支持 NVT/NPT/NVE 等系综的经典分子动力学模拟。
- **第一性原理 (CASTEP)**：支持直接执行单点能（Energy）、几何优化（GeometryOptimization）与能带结构（BandStructure）DFT 计算。
- **X射线衍射 (Reflex)**：支持选择靶材辐射源（如 Cu K$\alpha$）模拟粉末衍射（XRD）图谱。

---

## 3. 环境要求与快速安装

### 系统要求
- **操作系统**：Windows 10 / 11 / Windows Server (x64)
- **模拟软件**：BIOVIA Materials Studio 2020 / 20.1 / 2021 或以上（支持 Server 或 Client 完整版）
- **Python 环境**：Python 3.10 或更高版本

### 安装步骤

建议克隆到本地独立目录并使用虚拟环境：

```powershell
# 1. 克隆代码仓库
git clone https://github.com/noc228076/materials-studio-mcp.git
cd materials-studio-mcp

# 2. 创建并激活虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. 安装依赖（以可编辑模式安装）
python -m pip install --upgrade pip
python -m pip install -e .
```

> **提示**：如果您习惯使用现代工具 `uv`，只需一行：
> ```powershell
> uv venv && uv pip install -e .
> ```

---

## 4. 主流 MCP 客户端配置教程（保姆级）

请将以下示例中的 `<项目根目录>` 替换为您本地克隆的实际路径（例如 `C:\\path\\to\\materials-studio-mcp`）。

> [!TIP]
> **两种标准启动方式任选其一**：
> - **方式 A（现代首选，推荐）：使用 `uv` 驱动**。无需记忆复杂的 Python 解释器绝对路径，`uv` 会自动定位项目目录并隔离运行。
> - **方式 B（传统标准）：直接指定虚拟环境 `python.exe`**。利用本项目的 `-m material_studio_mcp_server` 模块化启动。

> [!IMPORTANT]
> **Windows 路径转义提示**：在 JSON 配置文件中，Windows 反斜杠 `\` 必须双写转义为 `\\`。

### 4.1 Claude Desktop（桌面端）
1. 打开 Claude Desktop 配置文件：
   - 快捷键 `Win + R` 输入 `%APPDATA%\Claude\claude_desktop_config.json` 打开文件。
2. 在 `mcpServers` 节点中加入本服务：

**推荐写法（使用 uv）：**
```json
{
  "mcpServers": {
    "material_studio_mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "<项目根目录>",
        "run",
        "material-studio-mcp-server"
      ]
    }
  }
}
```

**传统写法（直接指定虚拟环境 Python）：**
```json
{
  "mcpServers": {
    "material_studio_mcp": {
      "command": "<项目根目录>\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "material_studio_mcp_server"
      ]
    }
  }
}
```
3. 完全退出并重启 Claude Desktop，在对话框右下角即可看到“小锤子”图标中已包含 16 个 Materials Studio 工具。

---

### 4.2 Claude Code（Anthropic 官方 CLI 工具）
在克隆后的项目根目录下打开终端，执行一键注册命令（二选一）：

```powershell
# 方式 A：使用 uv（推荐）
claude mcp add material_studio_mcp_server uv -- --directory (Get-Location).Path run material-studio-mcp-server -s user

# 方式 B：使用虚拟环境 Python
$repo = (Resolve-Path .).Path
claude mcp add material_studio_mcp_server "$repo\.venv\Scripts\python.exe" -m material_studio_mcp_server -s user
```

验证连接状态：
```powershell
claude mcp list
# 输出包含：material_studio_mcp_server ... ✓ Connected
```

---

### 4.3 Cursor 编辑器
1. 打开 Cursor 设置：`Ctrl + ,` 或点击右上角齿轮 -> `Features` -> `MCP`。
2. 点击 **+ Add New MCP Server**：
   - **Name**: `material_studio_mcp`
   - **Type**: `command`
   - **Command（方案 A - uv 推荐）**: `uv --directory "<项目根目录>" run material-studio-mcp-server`
   - *(或方案 B - 虚拟环境)*: `<项目根目录>\.venv\Scripts\python.exe -m material_studio_mcp_server`
3. 保存后，Cursor 会显示状态指示灯为绿色，即可在 Composer 中指挥 AI 调度 Materials Studio。

---

### 4.4 VS Code (Cline / Roo Code 插件)
1. 打开插件的 MCP 设置界面（点击插件面板齿轮 -> `MCP Servers`）或直接编辑配置文件：
   - Roo Code / Cline 配置文件路径通常位于：`%APPDATA%\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\cline_mcp_settings.json`
2. 添加配置：

```json
{
  "mcpServers": {
    "material_studio_mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "<项目根目录>",
        "run",
        "material-studio-mcp-server"
      ]
    }
  }
}
```

---

### 4.5 Cherry Studio / Chatbox 等第三方桌面端
- **传输类型**：`stdio`
- **可执行文件 (Command)**：`uv`（或 `<项目根目录>\.venv\Scripts\python.exe`）
- **参数 (Args)**：`--directory <项目根目录> run material-studio-mcp-server`（或 `-m material_studio_mcp_server`）

---

## 5. Materials Studio 本地环境探测原理

服务启动时，会自动智能扫描本机常见的 Materials Studio 安装位置与注册表特征：
- 自动定位 `RunMatScript.bat`，如：
  ```text
  <Materials Studio 安装目录>\etc\Scripting\bin\RunMatScript.bat
  例如：C:\Program Files\BIOVIA\Materials Studio 2020\etc\Scripting\bin\RunMatScript.bat
  ```
- 自动定位官方结构库路径 `share\Structures`。

通常**无需手动配置任何系统环境变量**即可开箱即用。若您的软件安装在非标准路径，可通过环境变量显式指定：
```powershell
# 手动指定运行器路径
$env:MATERIAL_STUDIO_RUNNER = "C:\YourCustomPath\Materials Studio\etc\Scripting\bin\RunMatScript.bat"
# 手动指定默认并行核数（例如 8 核）
$env:MATERIAL_STUDIO_CORES = "8"
```

## 6. 可用工具全景（共 16 个核心工具）

### 1. 结构库与分子模板
- `material_studio_list_molecule_templates`：查看内置标准分子模板（水、甲烷、苯、TNT、乙醇等）。
- `material_studio_search_builtin_structures`：模糊检索 Materials Studio 官方结构库（`share/Structures`），包含金属、半导体、沸石、催化剂、有机物等。
- `material_studio_load_builtin_structure`：从官方结构库直接复制或转换导出结构文件（支持自动转换为 `.xsd`）。

### 2. 分子与周期性晶体/表面建模
- `material_studio_build_molecule`：使用 MaterialsScript 官方 `CreateAtom/CreateBond` 自动构建分子模型（支持自定义坐标或使用内置模板），无需手写易损坏的 XML。
- `material_studio_build_crystal`：基于三维晶胞参数（$a, b, c, \alpha, \beta, \gamma$）、分数坐标和空间群（如 `F m -3 m`）精准构建周期性晶体。
- `material_studio_build_supercell`：将已有晶体沿晶胞基矢扩展为超胞（如 $2\times2\times2$、$3\times3\times1$）。
- `material_studio_build_surface_slab`：沿指定密勒指数（$h, k, l$）进行表面切片（Cleave Surface）并构建真空层（Vacuum Slab）。
- `material_studio_build_tnt`：直接一键生成高精度 2,4,6-三硝基甲苯（TNT）模型，可选 Forcite 力场优化（保持向后兼容）。

### 3. 模拟计算与性能表征
- `material_studio_forcite_geometry_optimization`：生成或执行 Forcite 分子力学几何优化（支持多核 `-np` 并行）。
- `material_studio_forcite_dynamics`：执行经典分子动力学模拟（支持 NVT、NPT、NVE 系综，控温器选择，可导出轨迹）。
- `material_studio_castep_calculate`：执行第一性原理 CASTEP DFT 计算（支持 Energy、GeometryOptimization、BandStructure 任务及多核并行加速）。
- `material_studio_castep_energy_script`：快速生成 CASTEP 单点能模板脚本。
- `material_studio_reflex_powder_diffraction`：模拟 X 射线粉末衍射（XRD）图谱，支持选择靶材辐射源（如 Cu K$\alpha$）与 $2\theta$ 扫描区间。

### 4. 辅助与底层工具
- `material_studio_get_status`：检查服务环境、Materials Studio Runner 路径、多核配置与官方结构库挂载状态。
- `material_studio_structure_summary`：快速解析结构晶胞常数、体积、密度、空间群、原子与键总数。
- `material_studio_import_export`：导入外部结构并转换为其他格式（支持 cif, car, msi, pdb, mol, xsd）。
- `material_studio_run_script`：在隔离工作区执行原生 MaterialsScript Perl 脚本（支持 `-np` 并行核数与 `-project` 模式）。
- `material_studio_validate_script`：静态语法检查 MaterialsScript 脚本。
- `material_studio_list_script_templates`：列出可用脚本模板。

## 7. 环境变量与高级配置

- `MATERIAL_STUDIO_CORES`：默认多核并行核数（等效于 RunMatScript 的 `-np <cores>`）。
- `MATERIAL_STUDIO_STRUCTURES`：自定义官方或用户结构库路径。
- `MATERIAL_STUDIO_RUNNER`：手动指定 `RunMatScript.bat` 的绝对路径（一般会自动探测）。
- `MATERIAL_STUDIO_SCRIPT_TIMEOUT`：单次脚本计算超时时间（默认 1800 秒）。

## 8. 验证与自动化测试

通过 `uv` 或 `pip` 运行完整测试套件（31 项测试全部通过）：

```powershell
uv run --with pytest pytest -v
```

## 9. 模块分层与项目结构

```text
materials-studio-mcp/
├── pyproject.toml                     # PEP 621 构建配置与依赖
├── run_server.py                      # 源码直跑启动入口
├── README.md                          # 说明文档
├── tests/                             # 自动化测试套件
│   ├── test_config.py                 # Runner 自动探测测试
│   ├── test_runner.py                 # 进程管理与多核加速测试
│   ├── test_scripts.py                # Perl 生成与分子模板测试
│   └── test_server.py                 # MCP 工具端点与 Dry-run 测试
└── src/
    └── material_studio_mcp_server/
        ├── __init__.py                # 统一包级对外导出
        ├── __main__.py                # python -m 模块化原生启动入口
        ├── config.py                  # 安装环境与官方结构库自动发现
        ├── models.py                  # Pydantic 输入参数模型与枚举规范
        ├── templates.py               # 预置分子模板定义（Water、TNT、Benzene 等）
        ├── runner.py                  # 执行引擎（进程管理、-np 多核调度、模拟日志解析）
        ├── scripts.py                 # 原生 MaterialsScript Perl 模板生成器
        └── server.py                  # FastMCP 工具注册与调度路由
```

## 10. 典型使用示例 (JSON Payload)

### 示例 1：使用内置模板生成分子并自动进行 Forcite 力场优化
```json
{
  "template": "water",
  "output_file": "./models/water_optimized.xsd",
  "optimize": true,
  "forcefield": "COMPASS"
}
```

### 示例 2：构建周期性晶体 (金红石 TiO2，带空间群)
```json
{
  "name": "Rutile_TiO2",
  "output_file": "./models/TiO2.xsd",
  "a": 4.5937,
  "b": 4.5937,
  "c": 2.9587,
  "fractional_atoms": [
    {"element": "Ti", "u": 0.0, "v": 0.0, "w": 0.0},
    {"element": "O", "u": 0.3053, "v": 0.3053, "w": 0.0}
  ],
  "space_group": "P 42/m n m"
}
```

### 示例 3：检索 Materials Studio 官方半导体结构库
```json
{
  "query": "Si",
  "category": "semiconductors",
  "max_results": 10
}
```

### 示例 4：8 核并行运行 CASTEP 几何优化
```json
{
  "input_file": "./models/TiO2.xsd",
  "output_file": "./models/TiO2_relaxed.xsd",
  "task": "GeometryOptimization",
  "functional": "PBE",
  "quality": "Fine",
  "cutoff_energy_ev": 450,
  "num_cores": 8
}
```

---

## 11. 常见问题与避坑指南 (FAQ)

### Q1: 提示 `Material Studio runner not found` 怎么办？
- 检查本机是否安装了 Materials Studio 2020 / 20.1。
- 如果安装在非默认磁盘或自定义目录，在系统或终端中设置环境变量：
  ```powershell
  $env:MATERIAL_STUDIO_RUNNER = "你的安装目录\etc\Scripting\bin\RunMatScript.bat"
  ```
- 也可通过调用 `material_studio_get_status` 查看已扫描的 1000+ 个候选路径。

### Q2: 提示 `License checkout failed` 许可证错误怎么处理？
- MaterialsScript 与图形界面共用 BIOVIA License Server。请确保本机的 License Administrator 服务已正常运行。
- 如果算力在服务器集群上，请确认本机指向了有效的许可服务端口（如 `27000@licenseserver`）。

### Q3: 为什么不要手写 `.xsd` 文件？
- `.xsd` 是 Materials Studio 内部专有的 XML Schema 拓展，包含了分子拓扑图结构、力场类型与内部二进制校验码。手写 XML 极易引发解析错误导致软件异常崩溃退出。
- 强烈建议通过 `material_studio_build_molecule`、`material_studio_build_crystal` 或 `material_studio_import_export` 由软件内核自动输出 `.xsd`。

### Q4: 怎样开启多核并行加速？
- 可以在调用计算工具（如 `material_studio_castep_calculate`、`material_studio_forcite_dynamics` 等）时直接传入参数 `"num_cores": 8`。
- 或设置全局环境变量 `$env:MATERIAL_STUDIO_CORES = "8"`，服务将自动为后续所有计算默认分配对应核数。


