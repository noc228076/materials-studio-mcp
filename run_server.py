"""Run the Material Studio MCP server from a source checkout.

This launcher lets MCP clients start the server without installing the package
or setting PYTHONPATH. It intentionally does not configure Materials Studio
paths; the server performs local discovery on startup.
"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from material_studio_mcp_server.server import main


if __name__ == "__main__":
    main()
