"""Subprocess runner for MaterialsScript jobs."""

from __future__ import annotations

import json
import os
import re
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from html import unescape
from typing import Any

from .config import MaterialStudioConfig, _split_windows_args, resolve_config, runner_candidates


JSON_BEGIN = "__MATERIAL_STUDIO_MCP_JSON_BEGIN__"
JSON_END = "__MATERIAL_STUDIO_MCP_JSON_END__"
DEFAULT_JOBS_DIR = ".material-studio-mcp/jobs"


class MaterialStudioError(RuntimeError):
    """Raised when Materials Studio automation cannot complete."""


@dataclass(frozen=True)
class ScriptRunResult:
    """Result of a MaterialsScript subprocess run."""

    command: list[str]
    job_id: str
    job_dir: Path
    script_path: Path
    return_code: int
    stdout: str
    stderr: str
    output_file: Path | None
    log_file: Path | None
    materials_output: str
    materials_log: str
    success: bool
    timed_out: bool
    parsed_json: Any | None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {
            "command": self.command,
            "job_id": self.job_id,
            "job_dir": str(self.job_dir),
            "script_path": str(self.script_path),
            "return_code": self.return_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "output_file": str(self.output_file) if self.output_file else None,
            "log_file": str(self.log_file) if self.log_file else None,
            "materials_output": self.materials_output,
            "materials_log": self.materials_log,
            "success": self.success,
            "timed_out": self.timed_out,
            "parsed_json": self.parsed_json,
        }


class MaterialStudioRunner:
    """Launch MaterialsScript Perl programs through the local MS runner."""

    def __init__(self, config: MaterialStudioConfig | None = None) -> None:
        self.config = config or resolve_config()

    def status(self) -> dict[str, Any]:
        """Return runner detection and workspace status."""

        runner = self.config.runner
        return {
            "connected": bool(runner and runner.exists()),
            "runner": str(runner) if runner else None,
            "runner_exists": bool(runner and runner.exists()),
            "runner_source": self.config.runner_source,
            "install_home": str(self.config.install_home) if self.config.install_home else None,
            "workspace_root": str(self.config.workspace_root),
            "default_timeout_seconds": self.config.default_timeout_seconds,
            "default_cores": self.config.default_cores,
            "builtin_structures_path": str(self.config.builtin_structures_path) if self.config.builtin_structures_path else None,
            "builtin_structures_available": bool(self.config.builtin_structures_path and self.config.builtin_structures_path.is_dir()),
            "extra_runner_args": list(self.config.extra_runner_args),
            "searched_candidates": [str(path) for path in runner_candidates()[:25]],
            "searched_candidate_count": len(runner_candidates()),
            "notes": [
                "Materials Studio 2020 is supported through MaterialsScript Perl launchers.",
                "Set MATERIAL_STUDIO_RUNNER if the runner is installed in a custom location.",
            ],
        }

    def run_script(
        self,
        script: str,
        *,
        args: list[str] | None = None,
        working_dir: str | Path | None = None,
        timeout_seconds: int | None = None,
        job_prefix: str = "msjob",
        keep_script_name: str = "script.pl",
        num_cores: int | None = None,
        project_mode: bool = False,
    ) -> ScriptRunResult:
        """Write a script to an isolated job directory and launch it."""

        runner = self.config.runner
        if not runner or not runner.exists():
            raise MaterialStudioError(
                "Materials Studio runner was not found. Set MATERIAL_STUDIO_RUNNER "
                "to RunMatserver.bat or RunMatScript.bat for your Materials Studio 2020 install."
            )

        job_dir = self._create_job_dir(working_dir, job_prefix)
        script_path = job_dir / keep_script_name
        script_path.write_text(script, encoding="utf-8")

        command = self._build_command(
            runner,
            script_path,
            args or [],
            num_cores=num_cores,
            project_mode=project_mode,
        )
        timeout = timeout_seconds or self.config.default_timeout_seconds
        env = os.environ.copy()
        env.setdefault("MATERIAL_STUDIO_MCP_JOB_DIR", str(job_dir))

        try:
            completed = subprocess.run(
                command,
                cwd=str(job_dir),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            stdout = completed.stdout
            stderr = completed.stderr
            return_code = completed.returncode
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            return_code = -1
            timed_out = True

        output_file = script_path.with_suffix(script_path.suffix + ".out")
        log_file = job_dir / f"{script_path.stem}MatStudioLog.htm"
        materials_output = _read_text_if_exists(output_file)
        materials_log = _read_text_if_exists(log_file)
        combined_output = "\n".join(part for part in (stdout, materials_output) if part)
        success = (not timed_out) and _materials_run_succeeded(return_code, materials_output, materials_log)

        parsed_json = extract_tagged_json(combined_output)
        extra_metrics = extract_simulation_metrics(combined_output, materials_log)
        if extra_metrics:
            if isinstance(parsed_json, dict):
                parsed_json.setdefault("metrics", extra_metrics)
            elif parsed_json is None:
                parsed_json = {"metrics": extra_metrics}

        return ScriptRunResult(
            command=command,
            job_id=job_dir.name,
            job_dir=job_dir,
            script_path=script_path,
            return_code=return_code,
            stdout=stdout,
            stderr=stderr,
            output_file=output_file if output_file.exists() else None,
            log_file=log_file if log_file.exists() else None,
            materials_output=materials_output,
            materials_log=_html_to_text(materials_log),
            success=success,
            timed_out=timed_out,
            parsed_json=parsed_json,
        )

    def _build_command(
        self,
        runner: Path,
        script_path: Path,
        args: list[str],
        *,
        num_cores: int | None = None,
        project_mode: bool = False,
    ) -> list[str]:
        template = os.environ.get("MATERIAL_STUDIO_COMMAND_TEMPLATE")
        if template:
            mapping = {
                "runner": str(runner),
                "script": script_path.stem,
                "script_path": str(script_path),
                "args": subprocess.list2cmdline(args),
            }
            command_line = template.format(**mapping)
            return _split_windows_args(command_line)

        is_runmatscript = runner.name.lower() == "runmatscript.bat"
        script_arg = script_path.stem if is_runmatscript else str(script_path)

        options: list[str] = []
        effective_cores = num_cores if num_cores is not None else self.config.default_cores
        if is_runmatscript:
            if effective_cores > 1:
                options.extend(["-np", str(effective_cores)])
            if project_mode:
                options.append("-project")

        command = [str(runner), *options, *self.config.extra_runner_args, script_arg]
        if args:
            command.append("--")
            command.extend(args)
        return command

    def _create_job_dir(self, working_dir: str | Path | None, job_prefix: str) -> Path:
        base = Path(working_dir).expanduser().resolve() if working_dir else self.config.workspace_root
        jobs_root = base / DEFAULT_JOBS_DIR
        jobs_root.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_prefix = re.sub(r"[^A-Za-z0-9_.-]+", "_", job_prefix).strip("._") or "msjob"
        job_dir = jobs_root / f"{safe_prefix}-{stamp}-{uuid.uuid4().hex[:8]}"
        job_dir.mkdir(parents=False, exist_ok=False)
        return job_dir


def extract_tagged_json(output: str) -> Any | None:
    """Extract a JSON block emitted between MCP tags."""

    start = output.find(JSON_BEGIN)
    if start < 0:
        return None
    start += len(JSON_BEGIN)
    end = output.find(JSON_END, start)
    if end < 0:
        return None
    raw = output[start:end].strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"parse_error": "Tagged JSON was not valid JSON.", "raw": raw}


def extract_simulation_metrics(output: str = "", log_text: str = "") -> dict[str, Any]:
    """Extract known computational chemistry metrics from MS log or stdout."""
    metrics: dict[str, Any] = {}
    combined = f"{output}\n{log_text}"

    castep_energy = re.search(
        r"Final\s+(?:free\s+)?energy(?:,\s*E)?\s*[:=]\s*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)\s*eV",
        combined,
        re.IGNORECASE,
    )
    if castep_energy:
        try:
            metrics["castep_final_energy_ev"] = float(castep_energy.group(1))
        except ValueError:
            pass

    castep_force = re.search(
        r"Final\s+RMS\s+(?:force|gradient)\s*[:=]\s*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)",
        combined,
        re.IGNORECASE,
    )
    if castep_force:
        try:
            metrics["castep_final_rms_force_ev_per_ang"] = float(castep_force.group(1))
        except ValueError:
            pass

    forcite_energy = re.search(
        r"Total\s+Energy\s*[:=]\s*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)\s*(kcal/mol|kJ/mol|eV)?",
        combined,
        re.IGNORECASE,
    )
    if forcite_energy:
        try:
            metrics["forcite_total_energy"] = float(forcite_energy.group(1))
            if forcite_energy.group(2):
                metrics["forcite_energy_unit"] = forcite_energy.group(2)
        except ValueError:
            pass

    rms_grad = re.search(
        r"RMS\s+(?:Force|Gradient)\s*[:=]\s*([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)",
        combined,
        re.IGNORECASE,
    )
    if rms_grad and "castep_final_rms_force_ev_per_ang" not in metrics:
        try:
            metrics["rms_gradient"] = float(rms_grad.group(1))
        except ValueError:
            pass

    return metrics


def perl_string(value: str | Path) -> str:
    """Return a Perl single-quoted string literal."""

    raw = str(value)
    return "'" + raw.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    for encoding in ("utf-8", "mbcs", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="replace")
        except LookupError:
            continue
        except OSError:
            return ""
    return ""


def _materials_run_succeeded(return_code: int, output: str, log_html: str) -> bool:
    if return_code != 0:
        return False
    combined = f"{output}\n{log_html}".lower()
    failure_markers = (
        "completion status: (fail)",
        "exiting matserver: status failed",
        "couldn't parse the script",
        "syntax error",
        "execution of -e aborted",
    )
    return not any(marker in combined for marker in failure_markers)


def _html_to_text(value: str) -> str:
    if not value:
        return ""
    text = re.sub(r"(?is)<br\s*/?>", "\n", value)
    text = re.sub(r"(?is)</tr>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", "", text)
    text = unescape(text)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())
