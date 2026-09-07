"""Configuration and runner detection for Materials Studio."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


RUNNER_ENV_VARS = (
    "MATERIAL_STUDIO_RUNNER",
    "MS_RUNNER",
    "BIOVIA_MATERIALS_STUDIO_RUNNER",
)

HOME_ENV_VARS = (
    "MATERIAL_STUDIO_HOME",
    "MS_HOME",
    "BIOVIA_MATERIALS_STUDIO_HOME",
)

RUNNER_NAMES = (
    "RunMatserver.bat",
    "RunMatServer.bat",
    "RunMatScript.bat",
    "MaterialsScript.bat",
)

COMMON_INSTALL_ROOTS = (
    r"C:\Program Files\BIOVIA",
    r"C:\Program Files (x86)\BIOVIA",
    r"D:\Program Files\BIOVIA",
    r"D:\Program Files (x86)\BIOVIA",
    r"E:\Program Files\BIOVIA",
    r"E:\Program Files (x86)\BIOVIA",
    r"C:\Program Files\Dassault Systemes",
    r"C:\Program Files (x86)\Dassault Systemes",
    r"D:\Program Files\Dassault Systemes",
    r"D:\Program Files (x86)\Dassault Systemes",
    r"C:\Program Files\Accelrys",
    r"C:\Program Files (x86)\Accelrys",
    r"D:\Program Files\Accelrys",
    r"D:\Program Files (x86)\Accelrys",
)

VERSION_NAMES = (
    "Materials Studio 20.1 x64 Server",
    "Materials Studio 20.1",
    "Materials Studio 2020",
    "Materials Studio 2020 x64 Server",
    "MaterialsStudio2020",
    "Materials Studio 2020 Client",
)


@dataclass(frozen=True)
class MaterialStudioConfig:
    """Resolved Materials Studio configuration."""

    runner: Path | None
    workspace_root: Path
    default_timeout_seconds: int
    install_home: Path | None
    runner_source: str
    extra_runner_args: tuple[str, ...]
    builtin_structures_path: Path | None = None
    default_cores: int = 1


def resolve_config(cwd: Path | None = None) -> MaterialStudioConfig:
    """Resolve Materials Studio configuration from env vars and common paths."""

    cwd = (cwd or Path.cwd()).resolve()
    workspace_root = Path(os.environ.get("MATERIAL_STUDIO_WORKSPACE", str(cwd))).resolve()
    timeout = _parse_timeout(os.environ.get("MATERIAL_STUDIO_SCRIPT_TIMEOUT"))
    install_home = _resolve_install_home()
    runner, source = _resolve_runner(install_home)
    extra_runner_args = tuple(_split_windows_args(os.environ.get("MATERIAL_STUDIO_RUNNER_ARGS", "")))
    builtin_structures = _resolve_builtin_structures(runner, install_home)
    default_cores = _parse_cores(os.environ.get("MATERIAL_STUDIO_CORES"))
    return MaterialStudioConfig(
        runner=runner,
        workspace_root=workspace_root,
        default_timeout_seconds=timeout,
        install_home=install_home,
        runner_source=source,
        extra_runner_args=extra_runner_args,
        builtin_structures_path=builtin_structures,
        default_cores=default_cores,
    )


def runner_candidates() -> list[Path]:
    """Return likely Materials Studio runner paths without checking existence."""

    candidates: list[Path] = []
    for env_var in RUNNER_ENV_VARS:
        value = os.environ.get(env_var)
        if value:
            candidates.append(Path(value))

    install_home = _resolve_install_home()
    if install_home:
        candidates.extend(_runner_candidates_for_home(install_home))

    for root in COMMON_INSTALL_ROOTS:
        root_path = Path(root)
        for version_name in VERSION_NAMES:
            candidates.extend(_runner_candidates_for_home(root_path / version_name))
        if root_path.exists():
            try:
                homes = root_path.glob("Materials Studio*")
            except OSError:
                homes = []
            for home in homes:
                candidates.extend(_runner_candidates_for_home(home))

    return _dedupe_paths(candidates)


def _resolve_runner(install_home: Path | None) -> tuple[Path | None, str]:
    for env_var in RUNNER_ENV_VARS:
        value = os.environ.get(env_var)
        if not value:
            continue
        runner = Path(value).expanduser().resolve()
        if runner.exists():
            return runner, env_var
        return runner, f"{env_var} (missing)"

    if install_home:
        found = _first_existing(_runner_candidates_for_home(install_home))
        if found:
            return found, "MATERIAL_STUDIO_HOME"

    found = _first_existing(runner_candidates())
    if found:
        return found, "common_install_paths"
    return None, "not_found"


def _resolve_install_home() -> Path | None:
    for env_var in HOME_ENV_VARS:
        value = os.environ.get(env_var)
        if value:
            return Path(value).expanduser().resolve()
    return None


def _runner_candidates_for_home(home: Path) -> list[Path]:
    subdirs = (
        Path("etc") / "Scripting" / "bin",
        Path("bin"),
        Path("share") / "bin",
        Path("Scripts"),
        Path(""),
    )
    return [home / subdir / name for subdir in subdirs for name in RUNNER_NAMES]


def _first_existing(paths: Iterable[Path]) -> Path | None:
    for path in paths:
        try:
            resolved = path.expanduser().resolve()
        except OSError:
            continue
        if resolved.exists():
            return resolved
    return None


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def _parse_timeout(raw: str | None) -> int:
    if raw is None or not raw.strip():
        return 3600
    try:
        value = int(raw)
    except ValueError:
        return 3600
    return max(1, min(value, 7 * 24 * 3600))


def _split_windows_args(raw: str) -> list[str]:
    """Split a Windows command-line fragment."""

    if not raw.strip():
        return []
    if os.name == "nt":
        return _command_line_to_argv(raw)

    import shlex

    return shlex.split(raw)


def _command_line_to_argv(raw: str) -> list[str]:
    """Use the Windows shell parser so quoted paths stay intact."""

    import ctypes

    argc = ctypes.c_int()
    shell32 = ctypes.windll.shell32
    kernel32 = ctypes.windll.kernel32
    shell32.CommandLineToArgvW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)]
    shell32.CommandLineToArgvW.restype = ctypes.POINTER(ctypes.c_wchar_p)
    argv = shell32.CommandLineToArgvW(raw, ctypes.byref(argc))
    if not argv:
        raise ValueError("Could not parse command-line arguments")
    try:
        return [argv[index] for index in range(argc.value)]
    finally:
        kernel32.LocalFree(argv)


def _parse_cores(raw: str | None) -> int:
    if not raw or not raw.strip():
        return 1
    try:
        val = int(raw.strip())
        return max(1, min(val, 256))
    except ValueError:
        return 1


def _resolve_builtin_structures(runner: Path | None, install_home: Path | None) -> Path | None:
    custom = os.environ.get("MATERIAL_STUDIO_STRUCTURES")
    if custom and Path(custom).expanduser().is_dir():
        return Path(custom).expanduser().resolve()

    if install_home:
        candidate = install_home / "share" / "Structures"
        if candidate.is_dir():
            return candidate.resolve()

    if runner:
        curr = runner.parent
        for _ in range(5):
            candidate = curr / "share" / "Structures"
            if candidate.is_dir():
                return candidate.resolve()
            if curr.exists():
                try:
                    for sibling in curr.glob("Materials Studio*"):
                        if sibling.is_dir() and (sibling / "share" / "Structures").is_dir():
                            return (sibling / "share" / "Structures").resolve()
                except OSError:
                    pass
            curr = curr.parent

    for root in COMMON_INSTALL_ROOTS:
        root_path = Path(root)
        if root_path.is_dir():
            try:
                for home in root_path.glob("Materials Studio*"):
                    candidate = home / "share" / "Structures"
                    if candidate.is_dir():
                        return candidate.resolve()
            except OSError:
                continue

    return None


config: MaterialStudioConfig = resolve_config()
