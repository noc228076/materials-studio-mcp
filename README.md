# Materials Studio MCP Server

MCP (Model Context Protocol) 服务器，为 AI 助手（如 Claude）提供与 Materials Studio 交互的能力，支持分子建模、仿真计算和结果分析。

## 功能概览

### 结构建模 (7 tools)
| 工具 | 说明 |
|---|---|
| `create_crystal` | 创建周期性晶体结构（指定空间群、晶格参数） |
| `create_molecule` | 从原子坐标创建分子结构 |
| `create_surface` | 从体相晶体创建表面 slab（指定 Miller 指数） |
| `import_structure` | 导入 .xsd/.cif/.mol/.car/.msi 文件 |
| `export_structure` | 导出为不同格式 |
| `get_structure_info` | 获取结构详细信息（组成、晶格、空间群） |
| `list_structures` | 列出目录中的 MS 结构文件 |

### 仿真计算 (9 tools)
| 工具 | 说明 |
|---|---|
| `run_forcite_geometry_optimization` | Forcite 几何优化（力场、精度可调） |
| `run_forcite_dynamics` | Forcite 分子动力学（NVE/NVT/NPT/NPH/NPzT） |
| `run_forcite_energy` | Forcite 单点能计算 |
| `run_castep_calculation` | CASTEP DFT 计算（PBE/PW91/LDA，能带/态密度） |
| `run_dmol3_calculation` | DMol3 DFT 计算（DND/DNP/TNP 基组） |
| `check_job_status` | 查询作业状态 |
| `list_jobs` | 列出所有已提交作业 |
| `cancel_job` | 取消作业 |

### 结果分析 (5 tools)
| 工具 | 说明 |
|---|---|
| `analyze_forcite_energy` | 分析能量组分（价键/非键/交叉项） |
| `analyze_structure_properties` | 计算体积、密度等结构性质 |
| `analyze_trajectory` | 分析 MD 轨迹（MSD/RDF） |
| `get_simulation_results` | 获取已完成的仿真结果 |

### 资源端点 (2 resources)
| 端点 | 说明 |
|---|---|
| `ms://info` | 服务器和连接状态信息 |
| `ms://modules` | 列出可用的 MS 模块 |

## 系统要求

- **操作系统**: Windows（Materials Studio 仅支持 Windows）
- **Python**: 3.10+
- **Materials Studio**: 2020 或更新版本（已安装并授权）
- **Dependencies**: `mcp>=1.0.0`, `numpy>=1.21.0`, `pywin32>=300`

## 安装

```bash
# 克隆或进入项目目录
cd Materials Studio MCP

# 安装依赖
pip install -r requirements.txt

# 安装项目（可编辑模式，便于开发）
pip install -e .
```

## 配置 Claude Desktop

在 Claude Desktop 的配置文件中添加 MCP 服务器：

**文件路径**:
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "materials-studio": {
      "command": "ms-mcp",
      "args": [],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

配置后重启 Claude Desktop。服务器会在启动时自动尝试连接 Materials Studio，若连接失败则工具仍可用，需通过 `connect_materials_studio` 手动连接。

## 使用示例

以下是通过 AI 助手与 Materials Studio 交互的典型工作流：

### 1. 创建晶体结构

> "请创建 Si 的金刚石结构，空间群 Fd-3m，晶格常数 5.43 Angstrom，并在 (0,0,0) 和 (1/4,1/4,1/4) 放置 Si 原子"

AI 会调用：
```
create_crystal(
    name="Si_diamond",
    space_group="Fd-3m",
    a=5.43, b=5.43, c=5.43,
    elements=["Si", "Si"],
    coordinates=[[0, 0, 0], [0.25, 0.25, 0.25]]
)
```

### 2. 几何优化

> "对 Si_diamond.xsd 进行 Forcite 几何优化，使用 COMPASSIII 力场"

AI 会调用：
```
run_forcite_geometry_optimization(
    structure_file="Si_diamond.xsd",
    force_field="COMPASSIII",
    quality="Fine"
)
```

### 3. 分子动力学

> "对优化后的结构进行 NPT 分子动力学模拟，300K，1个大气压，100ps"

AI 会调用：
```
run_forcite_dynamics(
    structure_file="Si_diamond_optimized.xsd",
    ensemble="NPT",
    temperature=300.0,
    pressure=0.0001,
    total_time=100.0,
    force_field="COMPASSIII"
)
```

### 4. 分析结果

> "分析优化后结构的能量组分"

AI 会调用：
```
analyze_forcite_energy(
    structure_file="Si_diamond_optimized.xsd",
    force_field="COMPASSIII"
)
```

### 5. DFT 计算

> "用 CASTEP 计算 Si 的能带结构，PBE 泛函，截断能 380eV"

AI 会调用：
```
run_castep_calculation(
    structure_file="Si_diamond.xsd",
    functional="PBE",
    task="Properties",
    cut_off_energy=380.0,
    properties=["BandStructure", "DensityOfStates"]
)
```

## 架构

```
┌─────────────────────────────────────────────────────┐
│                    AI Assistant (Claude)              │
│  理解自然语言 → 选择合适的 MCP 工具 → 组织输出      │
└──────────────────────┬──────────────────────────────┘
                       │ MCP Protocol (JSON-RPC)
┌──────────────────────▼──────────────────────────────┐
│              Materials Studio MCP Server              │
│                                                       │
│  ┌──────────────────────────────────────────────┐    │
│  │  FastMCP (mcp.server.fastmcp)                │    │
│  │  • 21 tools + 2 resources                    │    │
│  └──────────────────┬───────────────────────────┘    │
│                     │                                 │
│  ┌──────────────────▼───────────────────────────┐    │
│  │  MaterialsStudioClient (ms_client.py)        │    │
│  │  • COM automation wrapper                    │    │
│  │  • Connection / Job management               │    │
│  └──────────────────┬───────────────────────────┘    │
│                     │ COM (pywin32)                    │
│  ┌──────────────────▼───────────────────────────┐    │
│  │  Materials Studio (BIOVIA/Dassault)           │    │
│  │  • Forcite, CASTEP, DMol3                     │    │
│  │  • 3D Atomistic document model                │    │
│  └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

## 项目结构

```
Materials Studio MCP/
├── pyproject.toml                        # 项目配置和依赖
├── requirements.txt                      # pip 依赖清单
├── README.md
└── src/materials_studio_mcp/
    ├── __init__.py
    ├── __main__.py                       # python -m 入口
    ├── server.py                         # MCP Server (FastMCP)
    ├── ms_client.py                      # MS COM API 封装层
    ├── models/
    │   ├── structures.py                 # 结构数据模型
    │   └── jobs.py                       # 作业数据模型
    ├── tools/
    │   ├── structures.py                 # 结构建模工具
    │   ├── simulation.py                 # 仿真计算工具
    │   └── analysis.py                   # 结果分析工具
    └── utils/
        └── file_ops.py                   # 文件操作工具
```

## 开发

```bash
# 安装开发模式
pip install -e .

# 验证工具注册
python -c "from materials_studio_mcp.server import mcp; tools = mcp._tool_manager.list_tools(); print(f'{len(tools)} tools registered'); [print(f'  - {t.name}') for t in tools]"

# 启动服务器（stdio 模式，默认）
ms-mcp
```

## 故障排除

| 问题 | 原因 | 解决 |
|---|---|---|
| 启动时 `MSConnectionError` | MS 未安装/未授权 | 确认 MS 已安装并激活，启动后手动调用 `connect_materials_studio` |
| `pywin32` 导入错误 | 缺少 Win32 COM 支持 | `pip install pywin32` |
| 工具返回 "Not connected" | MS COM 连接断开 | 调用 `connect_materials_studio(visible=True)` 检查 GUI 状态 |
| 作业一直 "running" | 仿真在 MS Gateway 后台运行 | 使用 `check_job_status` 轮询；在 MS GUI 中查看作业 Gateway |

## 许可证

MIT
