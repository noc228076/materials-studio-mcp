"""
Materials Studio MCP Server
===========================
MCP (Model Context Protocol) server for Materials Studio.
Provides AI agents with tools for molecular modeling, simulation, and analysis.
"""

from __future__ import annotations
import sys
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from materials_studio_mcp.ms_client import MaterialsStudioClient, MSConnectionError
from materials_studio_mcp.tools.structures import register_structure_tools
from materials_studio_mcp.tools.simulation import register_simulation_tools
from materials_studio_mcp.tools.analysis import register_analysis_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("ms-mcp")

mcp = FastMCP(
    "Materials Studio MCP",
    instructions="Molecular modeling and simulation via Materials Studio",
)

ms_client = MaterialsStudioClient(visible=False)


@mcp.resource("ms://info")
def get_server_info() -> str:
    """Get server and connection information."""
    connected = ms_client.is_connected
    return (
        f"Materials Studio MCP Server\n"
        f"  Status: {'Connected' if connected else 'Disconnected'}\n"
        f"  Version: 0.1.0\n"
        f"  Platform: Windows\n"
        f"  Tools: Structure creation, simulation (Forcite/CASTEP/DMol3), analysis\n"
        f"  Supported formats: .xsd, .cif, .mol, .car, .msi"
    )


@mcp.resource("ms://modules")
def list_available_modules() -> str:
    """List available Materials Studio modules."""
    if not ms_client.is_connected:
        return "Not connected to Materials Studio. Run 'connect' first."
    try:
        modules = ms_client._app.Modules
        available = []
        for m_name in ["Forcite", "CASTEP", "DMol3"]:
            try:
                getattr(modules, m_name)
                available.append(m_name)
            except AttributeError:
                continue
        return "Available modules:\n" + "\n".join(f"  - {m}" for m in available)
    except Exception as e:
        return f"Could not enumerate modules: {e}"


@mcp.tool()
def connect_materials_studio(visible: bool = False) -> str:
    """
    Connect to a running instance of Materials Studio.

    Args:
        visible: Whether to make the Materials Studio GUI visible
    """
    try:
        ms_client._visible = visible
        ms_client.connect()
        return f"Connected to Materials Studio (visible={visible})"
    except MSConnectionError as e:
        return f"Connection failed: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


@mcp.tool()
def disconnect_materials_studio() -> str:
    """Disconnect from Materials Studio."""
    try:
        ms_client.disconnect()
        return "Disconnected from Materials Studio"
    except Exception as e:
        return f"Error: {e}"


register_structure_tools(mcp, ms_client)
register_simulation_tools(mcp, ms_client)
register_analysis_tools(mcp, ms_client)


def main():
    """Run the MCP server."""
    logger.info("Starting Materials Studio MCP server...")
    try:
        ms_client.connect()
        logger.info("Connected to Materials Studio")
    except MSConnectionError as e:
        logger.warning(f"Could not connect to MS at startup: {e}")
        logger.warning("Tools will be available, but MS functions require manual connect")
    except Exception as e:
        logger.warning(f"Startup connection failed: {e}")

    mcp.run()


if __name__ == "__main__":
    main()
