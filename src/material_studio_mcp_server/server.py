"""MCP server exposing BIOVIA Materials Studio MaterialsScript tools."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

from .runner import MaterialStudioError, MaterialStudioRunner
from .scripts import (
    build_molecule_script,
    castep_energy_script,
    forcite_geometry_optimization_script,
    import_export_script,
    structure_summary_script,
    template_catalog,
    validate_materialscript,
)


mcp = FastMCP("material_studio_mcp")
runner = MaterialStudioRunner()


class ResponseFormat(str, Enum):
    """Supported response formats."""

    JSON = "json"
    MARKDOWN = "markdown"


class ForciteQuality(str, Enum):
    """Common Forcite quality values."""

    COARSE = "Coarse"
    MEDIUM = "Medium"
    FINE = "Fine"
    ULTRA_FINE = "Ultra-fine"


class ForciteConvergence(str, Enum):
    """Common Forcite convergence values."""

    COARSE = "Coarse"
    MEDIUM = "Medium"
    FINE = "Fine"
    ULTRA_FINE = "Ultra-fine"


class BondType(str, Enum):
    """MaterialsScript bond types accepted by CreateBond."""

    SINGLE = "Single"
    AROMATIC = "Aromatic"
    PARTIAL_DOUBLE = "Partial double"
    DOUBLE = "Double"
    TRIPLE = "Triple"


class RunScriptInput(BaseModel):
    """Input for running custom MaterialsScript Perl."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    script: str = Field(..., description="MaterialsScript Perl source code.", min_length=1, max_length=500_000)
    args: list[str] = Field(default_factory=list, description="Command-line arguments passed to the Perl script.", max_length=100)
    working_dir: str | None = Field(
        default=None,
        description="Optional base folder for the generated isolated job directory.",
        max_length=500,
    )
    timeout_seconds: int | None = Field(default=None, description="Execution timeout in seconds.", ge=1, le=7 * 24 * 3600)
    job_prefix: str = Field(default="custom", description="Prefix for the generated job directory.", min_length=1, max_length=50)
    dry_run: bool = Field(default=False, description="If true, return the script and planned config without launching Materials Studio.")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Return format.")


class ValidateScriptInput(BaseModel):
    """Input for MaterialsScript validation."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    script: str = Field(..., description="MaterialsScript Perl source code to check.", min_length=1, max_length=500_000)


class ImportExportInput(BaseModel):
    """Input for import/export conversion."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source_file: str = Field(..., description="Structure file to import, for example D:\\models\\CHA.cif.", min_length=1, max_length=500)
    output_file: str = Field(..., description="Target document path, for example D:\\models\\CHA.xsd.", min_length=1, max_length=500)
    working_dir: str | None = Field(default=None, description="Optional base folder for the generated isolated job directory.", max_length=500)
    timeout_seconds: int | None = Field(default=None, description="Execution timeout in seconds.", ge=1, le=7 * 24 * 3600)
    dry_run: bool = Field(default=False, description="If true, return the generated Perl without launching Materials Studio.")


class StructureSummaryInput(BaseModel):
    """Input for structure summary."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source_file: str = Field(..., description="Structure file to import and summarize.", min_length=1, max_length=500)
    working_dir: str | None = Field(default=None, description="Optional base folder for the generated isolated job directory.", max_length=500)
    timeout_seconds: int | None = Field(default=None, description="Execution timeout in seconds.", ge=1, le=7 * 24 * 3600)
    dry_run: bool = Field(default=False, description="If true, return the generated Perl without launching Materials Studio.")


class ForciteGeometryOptimizationInput(BaseModel):
    """Input for Forcite geometry optimization."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    input_file: str = Field(..., description="Structure file to import, for example D:\\models\\zeolite.xsd.", min_length=1, max_length=500)
    output_file: str | None = Field(default=None, description="Optional optimized structure export path.", max_length=500)
    forcefield: str = Field(default="COMPASS", description="Forcite forcefield name, for example COMPASS or COMPASSII.", min_length=1, max_length=100)
    quality: ForciteQuality = Field(default=ForciteQuality.MEDIUM, description="Forcite calculation quality.")
    charge_assignment: str = Field(default="Forcefield assigned", description="Forcite charge assignment mode.", min_length=1, max_length=100)
    max_iterations: int = Field(default=500, description="Maximum geometry optimization iterations.", ge=1, le=1_000_000)
    convergence: ForciteConvergence = Field(default=ForciteConvergence.MEDIUM, description="Forcite convergence level.")
    working_dir: str | None = Field(default=None, description="Optional base folder for the generated isolated job directory.", max_length=500)
    timeout_seconds: int | None = Field(default=None, description="Execution timeout in seconds.", ge=1, le=7 * 24 * 3600)
    dry_run: bool = Field(default=False, description="If true, return generated Perl without launching Materials Studio.")


class MoleculeAtom(BaseModel):
    """Atom specification for MaterialsScript molecule building."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str = Field(..., description="Unique atom ID used by bonds, for example C1.", min_length=1, max_length=50)
    element: str = Field(..., description="Element symbol, for example C, H, N, O.", min_length=1, max_length=3)
    x: float = Field(..., description="X coordinate in Angstrom.")
    y: float = Field(..., description="Y coordinate in Angstrom.")
    z: float = Field(..., description="Z coordinate in Angstrom.")


class MoleculeBond(BaseModel):
    """Bond specification for MaterialsScript molecule building."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    atom1: str = Field(..., description="First atom ID.", min_length=1, max_length=50)
    atom2: str = Field(..., description="Second atom ID.", min_length=1, max_length=50)
    type: BondType = Field(default=BondType.SINGLE, description="MaterialsScript bond type.")


class BuildMoleculeInput(BaseModel):
    """Input for creating a molecule document with MaterialsScript."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(default="Molecule", description="Document/molecule name.", min_length=1, max_length=120)
    output_file: str = Field(..., description="Output .xsd path written by Materials Studio Export.", min_length=1, max_length=500)
    atoms: list[MoleculeAtom] = Field(..., description="Atoms to create with Documents->New/CreateAtom.", min_length=1, max_length=500)
    bonds: list[MoleculeBond] = Field(default_factory=list, description="Bonds to create with CreateBond.", max_length=800)
    optimize: bool = Field(default=False, description="If true, run Forcite geometry optimization after building.")
    forcefield: str | None = Field(default="COMPASS", description="Optional Forcite forcefield if optimize=true.", max_length=100)
    quality: ForciteQuality = Field(default=ForciteQuality.MEDIUM, description="Optional Forcite quality if optimize=true.")
    max_iterations: int = Field(default=500, description="Forcite max iterations if optimize=true.", ge=1, le=1_000_000)
    working_dir: str | None = Field(default=None, description="Optional base folder for the generated isolated job directory.", max_length=500)
    timeout_seconds: int | None = Field(default=None, description="Execution timeout in seconds.", ge=1, le=7 * 24 * 3600)
    dry_run: bool = Field(default=False, description="If true, return generated Perl without launching Materials Studio.")


class CastepEnergyInput(BaseModel):
    """Input for CASTEP Energy script generation."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    input_file: str = Field(..., description="Structure file imported by the CASTEP Energy script.", min_length=1, max_length=500)
    quality: str = Field(default="Medium", description="CASTEP quality setting.", min_length=1, max_length=100)
    task: str = Field(default="Energy", description="CASTEP task name.", min_length=1, max_length=100)
    functional: str = Field(default="PBE", description="Exchange-correlation functional setting.", min_length=1, max_length=100)
    cutoff_energy_ev: int | None = Field(default=None, description="Optional cutoff energy in eV.", ge=1, le=100_000)
    kpoint_separation: float | None = Field(default=None, description="Optional k-point separation.", gt=0, le=10)


def _ok(result: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, **result}


def _error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, MaterialStudioError):
        return {"ok": False, "error": str(exc)}
    if isinstance(exc, ValueError):
        return {"ok": False, "error": str(exc)}
    return {
        "ok": False,
        "error": f"Unexpected {type(exc).__name__}: {exc}. Check the Materials Studio runner path and license state.",
    }


def _dry_run(script: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return _ok({"dry_run": True, "script": script, **(extra or {})})


def _path_warning(path: str, label: str) -> list[str]:
    if Path(path).expanduser().exists():
        return []
    return [f"{label} does not exist on this machine. Dry-run is still useful; execution will likely fail until the path is corrected."]


def _format_run_result(result: dict[str, Any], response_format: ResponseFormat) -> dict[str, Any]:
    if response_format == ResponseFormat.JSON:
        return _ok({"result": result})

    lines = [
        "# Materials Studio Script Result",
        "",
        f"- Return code: {result['return_code']}",
        f"- Success: {result['success']}",
        f"- Timed out: {result['timed_out']}",
        f"- Job directory: {result['job_dir']}",
        f"- Script: {result['script_path']}",
    ]
    if result.get("parsed_json") is not None:
        lines.extend(["", "## Parsed JSON", "", "```json", str(result["parsed_json"]), "```"])
    if result.get("stdout"):
        lines.extend(["", "## stdout", "", "```text", result["stdout"][-4000:], "```"])
    if result.get("materials_output"):
        lines.extend(["", "## MaterialsScript output", "", "```text", result["materials_output"][-4000:], "```"])
    if result.get("stderr"):
        lines.extend(["", "## stderr", "", "```text", result["stderr"][-4000:], "```"])
    if result.get("materials_log"):
        lines.extend(["", "## Materials Studio log", "", "```text", result["materials_log"][-4000:], "```"])
    return _ok({"markdown": "\n".join(lines), "result": result})


def _validate_molecule_graph(atoms: list[MoleculeAtom], bonds: list[MoleculeBond]) -> None:
    atom_ids = [atom.id for atom in atoms]
    unique_ids = set(atom_ids)
    if len(unique_ids) != len(atom_ids):
        raise ValueError("Atom IDs must be unique.")
    referenced = {bond.atom1 for bond in bonds} | {bond.atom2 for bond in bonds}
    missing = sorted(referenced - unique_ids)
    if missing:
        raise ValueError(f"Bonds reference unknown atom IDs: {', '.join(missing)}")


def _run_build_script(params: BuildMoleculeInput) -> dict[str, Any]:
    _validate_molecule_graph(params.atoms, params.bonds)
    script = build_molecule_script(
        params.name,
        params.output_file,
        [atom.model_dump() for atom in params.atoms],
        [
            {"atom1": bond.atom1, "atom2": bond.atom2, "type": bond.type.value}
            for bond in params.bonds
        ],
        optimize=params.optimize,
        forcefield=params.forcefield,
        quality=params.quality.value,
        max_iterations=params.max_iterations,
    )
    if params.dry_run:
        return _dry_run(script)
    try:
        result = runner.run_script(
            script,
            working_dir=params.working_dir,
            timeout_seconds=params.timeout_seconds,
            job_prefix="build_molecule",
        )
        return _ok({"result": result.to_dict()})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="material_studio_get_status",
    annotations={
        "title": "Get Materials Studio runner status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_get_status() -> dict[str, Any]:
    """Get BIOVIA Materials Studio automation status.

    Returns:
        dict[str, Any]: JSON-serializable status with keys:
            - ok (bool): whether the MCP tool succeeded
            - connected (bool): whether a runner executable was found
            - runner (str | None): resolved RunMatserver/RunMatScript path
            - workspace_root (str): base folder used for generated job folders
            - searched_candidates (list[str]): runner paths checked
    """

    return _ok(runner.status())


@mcp.tool(
    name="material_studio_list_script_templates",
    annotations={
        "title": "List built-in MaterialsScript templates",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_list_script_templates() -> dict[str, Any]:
    """List built-in MaterialsScript workflow templates.

    Returns:
        dict[str, Any]: JSON-serializable object with a templates list.
    """

    return _ok({"templates": template_catalog()})


@mcp.tool(
    name="material_studio_validate_script",
    annotations={
        "title": "Validate MaterialsScript source",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_validate_script(
    script: Annotated[
        str,
        Field(description="MaterialsScript Perl source code to check.", min_length=1, max_length=500_000),
    ],
) -> dict[str, Any]:
    """Validate MaterialsScript Perl source with lightweight checks.

    Args:
        script (str): Perl source code to check.

    Returns:
        dict[str, Any]: JSON object with valid, errors, and warnings fields.
    """

    params = ValidateScriptInput(script=script)
    return _ok(validate_materialscript(params.script))


@mcp.tool(
    name="material_studio_run_script",
    annotations={
        "title": "Run MaterialsScript Perl",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
def material_studio_run_script(
    script: Annotated[
        str,
        Field(description="MaterialsScript Perl source code.", min_length=1, max_length=500_000),
    ],
    args: Annotated[
        list[str] | None,
        Field(description="Command-line arguments passed to the Perl script.", max_length=100),
    ] = None,
    working_dir: Annotated[
        str | None,
        Field(description="Optional base folder for the generated isolated job directory.", max_length=500),
    ] = None,
    timeout_seconds: Annotated[
        int | None,
        Field(description="Execution timeout in seconds.", ge=1, le=7 * 24 * 3600),
    ] = None,
    job_prefix: Annotated[
        str,
        Field(description="Prefix for the generated job directory.", min_length=1, max_length=50),
    ] = "custom",
    dry_run: Annotated[
        bool,
        Field(description="If true, return the script and planned config without launching Materials Studio."),
    ] = False,
    response_format: Annotated[ResponseFormat, Field(description="Return format.")] = ResponseFormat.JSON,
) -> dict[str, Any]:
    """Run a custom MaterialsScript Perl program through Materials Studio.

    This is a powerful local automation tool. The script runs with the current
    user's privileges and may create, modify, or delete files depending on its
    Perl code and Materials Studio module calls.

    Args:
        script (str): MaterialsScript Perl source code.
        args (list[str] | None): optional command-line args.
        working_dir (str | None): optional job base directory.
        timeout_seconds (int | None): execution timeout.
        dry_run (bool): return script without execution.

    Returns:
        dict[str, Any]: run metadata, stdout/stderr, and tagged JSON if present.
    """

    params = RunScriptInput(
        script=script,
        args=args or [],
        working_dir=working_dir,
        timeout_seconds=timeout_seconds,
        job_prefix=job_prefix,
        dry_run=dry_run,
        response_format=response_format,
    )
    validation = validate_materialscript(params.script)
    if params.dry_run:
        return _dry_run(params.script, {"validation": validation})
    try:
        result = runner.run_script(
            params.script,
            args=params.args,
            working_dir=params.working_dir,
            timeout_seconds=params.timeout_seconds,
            job_prefix=params.job_prefix,
        )
        return _format_run_result(result.to_dict(), params.response_format)
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="material_studio_import_export",
    annotations={
        "title": "Import and export a Materials Studio document",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_import_export(
    source_file: Annotated[
        str,
        Field(description="Structure file to import, for example D:\\models\\CHA.cif.", min_length=1, max_length=500),
    ],
    output_file: Annotated[
        str,
        Field(description="Target document path, for example D:\\models\\CHA.xsd.", min_length=1, max_length=500),
    ],
    working_dir: Annotated[
        str | None,
        Field(description="Optional base folder for the generated isolated job directory.", max_length=500),
    ] = None,
    timeout_seconds: Annotated[
        int | None,
        Field(description="Execution timeout in seconds.", ge=1, le=7 * 24 * 3600),
    ] = None,
    dry_run: Annotated[
        bool,
        Field(description="If true, return the generated Perl without launching Materials Studio."),
    ] = False,
) -> dict[str, Any]:
    """Import a structure and export it to another supported format.

    Args:
        source_file (str): file path imported by Documents->Import.
        output_file (str): file path written by $doc->Export.
        dry_run (bool): return generated Perl without execution.

    Returns:
        dict[str, Any]: run metadata and parsed tagged JSON when successful.
    """

    params = ImportExportInput(
        source_file=source_file,
        output_file=output_file,
        working_dir=working_dir,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
    )
    script = import_export_script(params.source_file, params.output_file)
    if params.dry_run:
        return _dry_run(script, {"warnings": _path_warning(params.source_file, "source_file")})
    try:
        result = runner.run_script(
            script,
            working_dir=params.working_dir,
            timeout_seconds=params.timeout_seconds,
            job_prefix="import_export",
        )
        return _ok({"result": result.to_dict()})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="material_studio_structure_summary",
    annotations={
        "title": "Summarize a Materials Studio structure",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_structure_summary(
    source_file: Annotated[
        str,
        Field(description="Structure file to import and summarize.", min_length=1, max_length=500),
    ],
    working_dir: Annotated[
        str | None,
        Field(description="Optional base folder for the generated isolated job directory.", max_length=500),
    ] = None,
    timeout_seconds: Annotated[
        int | None,
        Field(description="Execution timeout in seconds.", ge=1, le=7 * 24 * 3600),
    ] = None,
    dry_run: Annotated[
        bool,
        Field(description="If true, return the generated Perl without launching Materials Studio."),
    ] = False,
) -> dict[str, Any]:
    """Import a structure and summarize basic document metadata.

    Args:
        source_file (str): file path imported by Documents->Import.
        dry_run (bool): return generated Perl without execution.

    Returns:
        dict[str, Any]: run metadata and parsed JSON fields such as atom_count.
    """

    params = StructureSummaryInput(
        source_file=source_file,
        working_dir=working_dir,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
    )
    script = structure_summary_script(params.source_file)
    if params.dry_run:
        return _dry_run(script, {"warnings": _path_warning(params.source_file, "source_file")})
    try:
        result = runner.run_script(
            script,
            working_dir=params.working_dir,
            timeout_seconds=params.timeout_seconds,
            job_prefix="summary",
        )
        return _ok({"result": result.to_dict()})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="material_studio_forcite_geometry_optimization",
    annotations={
        "title": "Run Forcite geometry optimization",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
def material_studio_forcite_geometry_optimization(
    input_file: Annotated[
        str,
        Field(description="Structure file to import, for example D:\\models\\zeolite.xsd.", min_length=1, max_length=500),
    ],
    output_file: Annotated[
        str | None,
        Field(description="Optional optimized structure export path.", max_length=500),
    ] = None,
    forcefield: Annotated[
        str,
        Field(description="Forcite forcefield name, for example COMPASS or COMPASSII.", min_length=1, max_length=100),
    ] = "COMPASS",
    quality: Annotated[ForciteQuality, Field(description="Forcite calculation quality.")] = ForciteQuality.MEDIUM,
    charge_assignment: Annotated[
        str,
        Field(description="Forcite charge assignment mode.", min_length=1, max_length=100),
    ] = "Forcefield assigned",
    max_iterations: Annotated[
        int,
        Field(description="Maximum geometry optimization iterations.", ge=1, le=1_000_000),
    ] = 500,
    convergence: Annotated[
        ForciteConvergence,
        Field(description="Forcite convergence level."),
    ] = ForciteConvergence.MEDIUM,
    working_dir: Annotated[
        str | None,
        Field(description="Optional base folder for the generated isolated job directory.", max_length=500),
    ] = None,
    timeout_seconds: Annotated[
        int | None,
        Field(description="Execution timeout in seconds.", ge=1, le=7 * 24 * 3600),
    ] = None,
    dry_run: Annotated[
        bool,
        Field(description="If true, return generated Perl without launching Materials Studio."),
    ] = False,
) -> dict[str, Any]:
    """Generate or run a Forcite GeometryOptimization MaterialsScript workflow.

    Args:
        input_file (str): structure imported by Materials Studio.
        output_file (str | None): optional optimized export path.
        forcefield (str): Forcite forcefield name.
        quality (ForciteQuality): calculation quality.
        max_iterations (int): maximum optimizer iterations.
        dry_run (bool): return generated Perl without execution.

    Returns:
        dict[str, Any]: dry-run script or run metadata with tagged JSON.
    """

    params = ForciteGeometryOptimizationInput(
        input_file=input_file,
        output_file=output_file,
        forcefield=forcefield,
        quality=quality,
        charge_assignment=charge_assignment,
        max_iterations=max_iterations,
        convergence=convergence,
        working_dir=working_dir,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
    )
    script = forcite_geometry_optimization_script(
        params.input_file,
        params.output_file,
        forcefield=params.forcefield,
        quality=params.quality.value,
        charge_assignment=params.charge_assignment,
        max_iterations=params.max_iterations,
        convergence=params.convergence.value,
    )
    if params.dry_run:
        return _dry_run(script, {"warnings": _path_warning(params.input_file, "input_file")})
    try:
        result = runner.run_script(
            script,
            working_dir=params.working_dir,
            timeout_seconds=params.timeout_seconds,
            job_prefix="forcite_go",
        )
        return _ok({"result": result.to_dict()})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="material_studio_build_molecule",
    annotations={
        "title": "Build a molecule with MaterialsScript",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_build_molecule(
    output_file: Annotated[
        str,
        Field(description="Output .xsd path written by Materials Studio Export.", min_length=1, max_length=500),
    ],
    atoms: Annotated[
        list[MoleculeAtom],
        Field(description="Atoms to create with CreateAtom.", min_length=1, max_length=500),
    ],
    bonds: Annotated[
        list[MoleculeBond] | None,
        Field(description="Bonds to create with CreateBond.", max_length=800),
    ] = None,
    name: Annotated[
        str,
        Field(description="Document/molecule name.", min_length=1, max_length=120),
    ] = "Molecule",
    optimize: Annotated[
        bool,
        Field(description="If true, run Forcite geometry optimization after building."),
    ] = False,
    forcefield: Annotated[
        str | None,
        Field(description="Optional Forcite forcefield if optimize=true.", max_length=100),
    ] = "COMPASS",
    quality: Annotated[
        ForciteQuality,
        Field(description="Optional Forcite quality if optimize=true."),
    ] = ForciteQuality.MEDIUM,
    max_iterations: Annotated[
        int,
        Field(description="Forcite max iterations if optimize=true.", ge=1, le=1_000_000),
    ] = 500,
    working_dir: Annotated[
        str | None,
        Field(description="Optional base folder for the generated isolated job directory.", max_length=500),
    ] = None,
    timeout_seconds: Annotated[
        int | None,
        Field(description="Execution timeout in seconds.", ge=1, le=7 * 24 * 3600),
    ] = None,
    dry_run: Annotated[
        bool,
        Field(description="If true, return generated Perl without launching Materials Studio."),
    ] = False,
) -> dict[str, Any]:
    """Build a molecular XSD through MaterialsScript CreateAtom/CreateBond.

    Use this instead of hand-writing .xsd XML. The output is created by
    Materials Studio itself and exported through the official document API.
    """

    params = BuildMoleculeInput(
        name=name,
        output_file=output_file,
        atoms=atoms,
        bonds=bonds or [],
        optimize=optimize,
        forcefield=forcefield,
        quality=quality,
        max_iterations=max_iterations,
        working_dir=working_dir,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
    )
    try:
        return _run_build_script(params)
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="material_studio_build_tnt",
    annotations={
        "title": "Build 2,4,6-trinitrotoluene",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_build_tnt(
    output_file: Annotated[
        str,
        Field(description="Output .xsd path for 2,4,6-trinitrotoluene.", min_length=1, max_length=500),
    ],
    optimize: Annotated[
        bool,
        Field(description="If true, run Forcite geometry optimization after building."),
    ] = False,
    working_dir: Annotated[
        str | None,
        Field(description="Optional base folder for the generated isolated job directory.", max_length=500),
    ] = None,
    timeout_seconds: Annotated[
        int | None,
        Field(description="Execution timeout in seconds.", ge=1, le=7 * 24 * 3600),
    ] = None,
    dry_run: Annotated[
        bool,
        Field(description="If true, return generated Perl without launching Materials Studio."),
    ] = False,
) -> dict[str, Any]:
    """Build 2,4,6-trinitrotoluene (TNT, C7H5N3O6) as an XSD document."""

    atoms = [
        MoleculeAtom(id="C1", element="C", x=1.400, y=0.000, z=0.000),
        MoleculeAtom(id="C2", element="C", x=0.700, y=1.212, z=0.000),
        MoleculeAtom(id="C3", element="C", x=-0.700, y=1.212, z=0.000),
        MoleculeAtom(id="C4", element="C", x=-1.400, y=0.000, z=0.000),
        MoleculeAtom(id="C5", element="C", x=-0.700, y=-1.212, z=0.000),
        MoleculeAtom(id="C6", element="C", x=0.700, y=-1.212, z=0.000),
        MoleculeAtom(id="C7", element="C", x=2.910, y=0.000, z=0.000),
        MoleculeAtom(id="H1", element="H", x=3.550, y=0.630, z=0.000),
        MoleculeAtom(id="H2", element="H", x=3.550, y=-0.315, z=0.546),
        MoleculeAtom(id="H3", element="H", x=3.550, y=-0.315, z=-0.546),
        MoleculeAtom(id="H4", element="H", x=-1.250, y=2.162, z=0.000),
        MoleculeAtom(id="H5", element="H", x=-1.250, y=-2.162, z=0.000),
        MoleculeAtom(id="N1", element="N", x=1.440, y=2.490, z=0.000),
        MoleculeAtom(id="O1", element="O", x=1.990, y=3.250, z=0.350),
        MoleculeAtom(id="O2", element="O", x=0.930, y=3.070, z=-0.350),
        MoleculeAtom(id="N2", element="N", x=-2.870, y=0.000, z=0.000),
        MoleculeAtom(id="O3", element="O", x=-3.610, y=-0.610, z=0.200),
        MoleculeAtom(id="O4", element="O", x=-3.610, y=0.610, z=-0.200),
        MoleculeAtom(id="N3", element="N", x=1.440, y=-2.490, z=0.000),
        MoleculeAtom(id="O5", element="O", x=1.990, y=-3.250, z=-0.350),
        MoleculeAtom(id="O6", element="O", x=0.930, y=-3.070, z=0.350),
    ]
    bonds = [
        MoleculeBond(atom1="C1", atom2="C2", type=BondType.AROMATIC),
        MoleculeBond(atom1="C2", atom2="C3", type=BondType.AROMATIC),
        MoleculeBond(atom1="C3", atom2="C4", type=BondType.AROMATIC),
        MoleculeBond(atom1="C4", atom2="C5", type=BondType.AROMATIC),
        MoleculeBond(atom1="C5", atom2="C6", type=BondType.AROMATIC),
        MoleculeBond(atom1="C6", atom2="C1", type=BondType.AROMATIC),
        MoleculeBond(atom1="C1", atom2="C7", type=BondType.SINGLE),
        MoleculeBond(atom1="C7", atom2="H1", type=BondType.SINGLE),
        MoleculeBond(atom1="C7", atom2="H2", type=BondType.SINGLE),
        MoleculeBond(atom1="C7", atom2="H3", type=BondType.SINGLE),
        MoleculeBond(atom1="C3", atom2="H4", type=BondType.SINGLE),
        MoleculeBond(atom1="C5", atom2="H5", type=BondType.SINGLE),
        MoleculeBond(atom1="C2", atom2="N1", type=BondType.SINGLE),
        MoleculeBond(atom1="N1", atom2="O1", type=BondType.DOUBLE),
        MoleculeBond(atom1="N1", atom2="O2", type=BondType.PARTIAL_DOUBLE),
        MoleculeBond(atom1="C4", atom2="N2", type=BondType.SINGLE),
        MoleculeBond(atom1="N2", atom2="O3", type=BondType.DOUBLE),
        MoleculeBond(atom1="N2", atom2="O4", type=BondType.PARTIAL_DOUBLE),
        MoleculeBond(atom1="C6", atom2="N3", type=BondType.SINGLE),
        MoleculeBond(atom1="N3", atom2="O5", type=BondType.DOUBLE),
        MoleculeBond(atom1="N3", atom2="O6", type=BondType.PARTIAL_DOUBLE),
    ]
    params = BuildMoleculeInput(
        name="TNT_246_trinitrotoluene",
        output_file=output_file,
        atoms=atoms,
        bonds=bonds,
        optimize=optimize,
        forcefield="COMPASS",
        quality=ForciteQuality.MEDIUM,
        max_iterations=500,
        working_dir=working_dir,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
    )
    try:
        return _run_build_script(params)
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="material_studio_castep_energy_script",
    annotations={
        "title": "Generate a CASTEP Energy script",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_castep_energy_script(
    input_file: Annotated[
        str,
        Field(description="Structure file imported by the CASTEP Energy script.", min_length=1, max_length=500),
    ],
    quality: Annotated[
        str,
        Field(description="CASTEP quality setting.", min_length=1, max_length=100),
    ] = "Medium",
    task: Annotated[
        str,
        Field(description="CASTEP task name.", min_length=1, max_length=100),
    ] = "Energy",
    functional: Annotated[
        str,
        Field(description="Exchange-correlation functional setting.", min_length=1, max_length=100),
    ] = "PBE",
    cutoff_energy_ev: Annotated[
        int | None,
        Field(description="Optional cutoff energy in eV.", ge=1, le=100_000),
    ] = None,
    kpoint_separation: Annotated[
        float | None,
        Field(description="Optional k-point separation.", gt=0, le=10),
    ] = None,
) -> dict[str, Any]:
    """Generate a CASTEP Energy MaterialsScript Perl template.

    This tool does not execute CASTEP. Use material_studio_run_script after
    reviewing the generated script and confirming the local CASTEP license and
    server queue settings are ready.

    Args:
        input_file (str): structure imported by the CASTEP Energy script.
        quality (str): CASTEP quality setting.
        task (str): CASTEP task name.
        functional (str): exchange-correlation functional.
        cutoff_energy_ev (int | None): optional cutoff energy in eV.
        kpoint_separation (float | None): optional k-point separation.

    Returns:
        dict[str, Any]: generated MaterialsScript Perl source code.
    """

    params = CastepEnergyInput(
        input_file=input_file,
        quality=quality,
        task=task,
        functional=functional,
        cutoff_energy_ev=cutoff_energy_ev,
        kpoint_separation=kpoint_separation,
    )
    script = castep_energy_script(
        params.input_file,
        quality=params.quality,
        task=params.task,
        functional=params.functional,
        cutoff_energy_ev=params.cutoff_energy_ev,
        kpoint_separation=params.kpoint_separation,
    )
    return _ok({"script": script})


def main() -> None:
    """Run the Materials Studio MCP server over stdio."""

    mcp.run()


if __name__ == "__main__":
    main()
