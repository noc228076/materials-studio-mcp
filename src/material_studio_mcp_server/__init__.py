from __future__ import annotations

from .config import MaterialStudioConfig, config, resolve_config
from .runner import MaterialStudioError, MaterialStudioRunner
from .server import main, mcp, runner

__all__ = [
    "__version__",
    "MaterialStudioConfig",
    "MaterialStudioError",
    "MaterialStudioRunner",
    "config",
    "main",
    "mcp",
    "resolve_config",
    "runner",
]

__version__ = "0.2.0"
