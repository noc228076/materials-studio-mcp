# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-09-07

### Added
- **Periodic Crystal & Surface Modeling**:
  - `material_studio_build_crystal`: Build 3D periodic crystal structures from lattice constants ($a, b, c, \alpha, \beta, \gamma$), fractional atomic coordinates, and international space groups (e.g. `P 42/m n m`).
  - `material_studio_build_supercell`: Expand crystal structures into supercells along lattice vectors (e.g. $2\times2\times2$, $3\times3\times1$).
  - `material_studio_build_surface_slab`: Cleave crystal surfaces along specified Miller indices ($h, k, l$) with customizable vacuum slab thickness.
- **DFT & Molecular Dynamics Simulation**:
  - `material_studio_castep_calculate`: First-principles DFT calculation supporting Energy, GeometryOptimization, and BandStructure tasks with customizable exchange-correlation functionals and cutoff energy.
  - `material_studio_forcite_dynamics`: Classical molecular dynamics simulation supporting NVT, NPT, and NVE ensembles with thermostat/barostat control and trajectory export.
  - `material_studio_reflex_powder_diffraction`: Powder X-ray diffraction (XRD) pattern simulation with multiple radiation sources (Cu Kα, Mo Kα, etc.) and customizable $2\theta$ range.
- **Official Structures Library & Molecular Templates**:
  - Auto-detection of BIOVIA Materials Studio official crystal structures directory (`share/Structures`).
  - `material_studio_search_builtin_structures`: Fuzzy keyword search over thousands of built-in crystals (metals, semiconductors, zeolites, catalysts).
  - `material_studio_load_builtin_structure`: One-click copy and format conversion for library structures into standard `.xsd`.
  - Decoupled molecular templates registry (`templates.py`) covering Water, Methane, Benzene, TNT, and Ethanol.
- **Multi-Core Acceleration**:
  - Full-pipeline parallel execution using `-np <cores>` and `MATERIAL_STUDIO_CORES` environment variable across all computation tools.
- **Packaging & Developer Experience**:
  - Added `material_studio_mcp_server/__main__.py` for native `python -m material_studio_mcp_server` and `uv run material-studio-mcp-server` invocation.
  - Added Hatchling / PEP 621 build configuration in `pyproject.toml`.

### Changed
- **Architectural Decoupling**:
  - Separated Pydantic models into `models.py` with strict Pydantic v2 validation and enums.
  - Separated molecular template assets into `templates.py`.
  - Refactored `runner.py`, `scripts.py`, and `server.py` into cohesive single-responsibility modules.
- **Testing**:
  - Expanded automated test suite from 11 to 31 tests covering unit testing, Perl generation, multi-core scheduling, and dry-run execution with 100% pass rate.
- **Documentation**:
  - Modernized `README.md` with dual client setup guides (`uv run` and `python -m`).
  - Completely sanitized all documentation and parameter schemas to prevent private path leakage.

### Removed
- Deleted `start-material-studio-mcp.cmd` to eliminate `spawn ENOENT` errors on Windows MCP clients and avoid stdio JSON-RPC stream corruption.
- Removed hardcoded TNT coordinates and monolithic script structure.

---

## [0.1.0] - 2026-09-06

### Added
- Initial proof-of-concept FastMCP server for BIOVIA Materials Studio automation.
- Basic MaterialsScript execution via `RunMatScript.bat`.
- Initial TNT generation and Forcite geometry optimization tools.
