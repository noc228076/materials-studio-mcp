from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

MS_EXTENSIONS = {
    ".xsd": "Materials Studio Structure Document",
    ".msi": "Materials Studio Initial Structure",
    ".cif": "Crystallographic Information File",
    ".mol": "MDL Molfile",
    ".sdf": "Structure Data File",
    ".car": "Accelrys CAR file",
    ".mdf": "Materials Studio MDF file",
    ".std": "Materials Studio STD file",
    ".xtd": "Materials Studio Trajectory File",
    ".his": "Materials Studio History File",
}


def resolve_ms_path(path: str) -> str:
    return os.path.abspath(path)


def ensure_ms_directory(path: str) -> str:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return str(p)


def get_ms_file_info(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"exists": False, "path": path}
    ext = p.suffix.lower()
    return {
        "exists": True,
        "path": str(p.absolute()),
        "name": p.name,
        "extension": ext,
        "format": MS_EXTENSIONS.get(ext, "Unknown"),
        "size_bytes": p.stat().st_size,
        "modified": p.stat().st_mtime,
    }


def list_working_directory(path: Optional[str] = None) -> list[dict]:
    if path is None:
        path = os.getcwd()
    results = []
    for f in Path(path).iterdir():
        if f.is_file() and f.suffix.lower() in MS_EXTENSIONS:
            results.append({
                "name": f.name,
                "path": str(f.absolute()),
                "format": MS_EXTENSIONS.get(f.suffix.lower(), "Unknown"),
                "size": f.stat().st_size,
            })
    return results
