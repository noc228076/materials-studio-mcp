"""MCP server exposing BIOVIA Materials Studio MaterialsScript tools."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Any

try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

from .config import config
from .runner import MaterialStudioError, MaterialStudioRunner
from .scripts import (
    MOLECULE_TEMPLATES,
    build_crystal_script,
    build_molecule_script,
    build_supercell_script,
    build_surface_slab_script,
    castep_calculate_script,
    castep_energy_script,
    forcite_dynamics_script,
    forcite_geometry_optimization_script,
    get_molecule_template,
    import_export_script,
    list_molecule_templates,
    reflex_powder_diffraction_script,
    structure_summary_script,
    template_catalog,
    validate_materialscript,
)


mcp = FastMCP("material_studio_mcp")
runner = MaterialStudioRunner()


from .models import (
    BondType,
    BuildCrystalInput,
    BuildMoleculeInput,
    BuildSupercellInput,
    BuildSurfaceSlabInput,
    CastepCalculateInput,
    CastepEnergyInput,
    CastepQuality,
    CastepTask,
    CrystalAtom,
    ForciteConvergence,
    ForciteDynamicsInput,
    ForciteEnsemble,
    ForciteGeometryOptimizationInput,
    ForciteQuality,
    ImportExportInput,
    MoleculeAtom,
    MoleculeBond,
    ReflexPowderDiffractionInput,
    ResponseFormat,
    RunScriptInput,
    StructureSummaryInput,
    ValidateScriptInput,
)


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
    atoms = params.atoms
    bonds = params.bonds or []
    name = params.name

    if params.template:
        tmpl = get_molecule_template(params.template)
        if not tmpl:
            available = ", ".join(MOLECULE_TEMPLATES.keys())
            raise ValueError(f"Unknown molecule template '{params.template}'. Available: {available}")
        if not atoms:
            atoms = [MoleculeAtom(**a) for a in tmpl["atoms"]]
            bonds = [MoleculeBond(**b) for b in tmpl.get("bonds", [])]
            if name == "Molecule":
                name = tmpl["name"]

    if not atoms:
        raise ValueError("Must provide either 'template' (e.g. 'water', 'benzene', 'tnt') or 'atoms' list.")

    _validate_molecule_graph(atoms, bonds)
    script = build_molecule_script(
        name,
        params.output_file,
        [atom.model_dump() for atom in atoms],
        [
            {"atom1": bond.atom1, "atom2": bond.atom2, "type": bond.type.value if hasattr(bond.type, "value") else str(bond.type)}
            for bond in bonds
        ],
        optimize=params.optimize,
        forcefield=params.forcefield,
        quality=params.quality.value if hasattr(params.quality, "value") else str(params.quality),
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
    num_cores: Annotated[
        int | None,
        Field(description="Parallel cores to allocate (-np).", ge=1, le=256),
    ] = None,
    project_mode: Annotated[
        bool,
        Field(description="Run script in Materials Studio project mode (-project)."),
    ] = False,
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
        num_cores (int | None): number of parallel cores (-np).
        project_mode (bool): whether to run in project mode (-project).
        dry_run (bool): return script without execution.

    Returns:
        dict[str, Any]: run metadata, stdout/stderr, and tagged JSON if present.
    """

    params = RunScriptInput(
        script=script,
        args=args or [],
        working_dir=working_dir,
        timeout_seconds=timeout_seconds,
        num_cores=num_cores,
        project_mode=project_mode,
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
            num_cores=params.num_cores,
            project_mode=params.project_mode,
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
        Field(description="Structure file to import, for example CHA.cif or ./models/CHA.cif.", min_length=1, max_length=500),
    ],
    output_file: Annotated[
        str,
        Field(description="Target document path, for example CHA.xsd or ./models/CHA.xsd.", min_length=1, max_length=500),
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
        Field(description="Structure file to import, for example zeolite.xsd or ./models/zeolite.xsd.", min_length=1, max_length=500),
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
    num_cores: Annotated[
        int | None,
        Field(description="Parallel cores to allocate (-np).", ge=1, le=256),
    ] = None,
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
        num_cores (int | None): parallel cores to allocate (-np).
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
        num_cores=num_cores,
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
            num_cores=params.num_cores,
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
        list[MoleculeAtom] | None,
        Field(description="Atoms to create with CreateAtom. Optional if template is provided.", max_length=500),
    ] = None,
    bonds: Annotated[
        list[MoleculeBond] | None,
        Field(description="Bonds to create with CreateBond.", max_length=800),
    ] = None,
    template: Annotated[
        str | None,
        Field(description="Optional built-in molecule template name (water, methane, benzene, tnt, ethanol).", max_length=100),
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
    Can build from custom atoms/bonds or from predefined templates (water, methane, benzene, tnt, ethanol).
    """

    params = BuildMoleculeInput(
        name=name,
        output_file=output_file,
        template=template,
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

    params = BuildMoleculeInput(
        name="TNT_246_trinitrotoluene",
        output_file=output_file,
        template="tnt",
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


@mcp.tool(
    name="material_studio_list_molecule_templates",
    annotations={
        "title": "List built-in molecule templates",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_list_molecule_templates() -> dict[str, Any]:
    """List all available predefined molecule templates (e.g. water, methane, benzene, tnt, ethanol)."""
    return _ok({"templates": list_molecule_templates()})


@mcp.tool(
    name="material_studio_search_builtin_structures",
    annotations={
        "title": "Search Materials Studio built-in structures",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_search_builtin_structures(
    query: Annotated[
        str,
        Field(description="Search term (case-insensitive filename/formula match, e.g. 'TiO2', 'Si', 'graphene', 'zeolite').", min_length=1, max_length=100),
    ],
    category: Annotated[
        str | None,
        Field(description="Optional category folder filter (e.g. 'metals', 'semiconductors', 'zeolites', 'ceramics').", max_length=100),
    ] = None,
    max_results: Annotated[
        int,
        Field(description="Maximum matching structures to return.", ge=1, le=200),
    ] = 50,
) -> dict[str, Any]:
    """Search the Materials Studio built-in structure library (share/Structures)."""
    base_dir = config.builtin_structures_path
    if not base_dir or not base_dir.is_dir():
        return _error(MaterialStudioError(f"Built-in structures directory not found or not configured: {base_dir}"))

    search_root = (base_dir / category) if category else base_dir
    if not search_root.is_dir():
        return _error(MaterialStudioError(f"Category folder does not exist: {category}"))

    query_lower = query.lower()
    matches = []
    extensions = {".msi", ".car", ".cell", ".xsd", ".cif", ".mol", ".pdb"}
    for path in search_root.rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions:
            if query_lower in path.name.lower():
                try:
                    rel = path.relative_to(base_dir).as_posix()
                except ValueError:
                    rel = path.name
                matches.append({
                    "name": path.stem,
                    "filename": path.name,
                    "relative_path": rel,
                    "absolute_path": str(path),
                    "extension": path.suffix.lower(),
                    "size_bytes": path.stat().st_size,
                })
                if len(matches) >= max_results:
                    break

    return _ok({
        "query": query,
        "category": category,
        "structures_root": str(base_dir),
        "total_matches": len(matches),
        "matches": matches,
    })


@mcp.tool(
    name="material_studio_load_builtin_structure",
    annotations={
        "title": "Load Materials Studio built-in structure",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_load_builtin_structure(
    relative_path: Annotated[
        str,
        Field(description="Relative path within share/Structures (e.g. 'semiconductors/Si.msi') or absolute path.", min_length=1, max_length=500),
    ],
    output_file: Annotated[
        str,
        Field(description="Destination file path where the structure will be copied/exported.", min_length=1, max_length=500),
    ],
    convert_to_xsd: Annotated[
        bool,
        Field(description="If true and format is not .xsd, convert to .xsd using Materials Studio document API."),
    ] = False,
    dry_run: Annotated[
        bool,
        Field(description="If true, return generated action/Perl without executing."),
    ] = False,
) -> dict[str, Any]:
    """Load and copy/convert a structure from the Materials Studio built-in structure library."""
    base_dir = config.builtin_structures_path
    target = Path(relative_path)
    if not target.is_absolute():
        if not base_dir:
            return _error(MaterialStudioError("Built-in structures directory is not configured."))
        target = base_dir / relative_path

    if not target.is_file():
        return _error(MaterialStudioError(f"Built-in structure file not found: {target}"))

    out_path = Path(output_file).expanduser().resolve()
    if convert_to_xsd and target.suffix.lower() != ".xsd":
        script = import_export_script(target, out_path)
        if dry_run:
            return _dry_run(script, {"source": str(target), "destination": str(out_path)})
        try:
            result = runner.run_script(script, job_prefix="load_structure")
            return _ok({"source": str(target), "destination": str(out_path), "result": result.to_dict()})
        except Exception as exc:
            return _error(exc)
    else:
        if dry_run:
            return _ok({"dry_run": True, "action": f"Copy {target} to {out_path}"})
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copyfile(target, out_path)
            return _ok({"source": str(target), "destination": str(out_path), "copied": True})
        except Exception as exc:
            return _error(exc)


@mcp.tool(
    name="material_studio_build_crystal",
    annotations={
        "title": "Build a 3D periodic crystal",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_build_crystal(
    output_file: Annotated[
        str,
        Field(description="Output .xsd path for the created crystal.", min_length=1, max_length=500),
    ],
    a: Annotated[
        float,
        Field(description="Lattice parameter a in Angstroms.", gt=0.1, le=1000.0),
    ],
    b: Annotated[
        float,
        Field(description="Lattice parameter b in Angstroms.", gt=0.1, le=1000.0),
    ],
    c: Annotated[
        float,
        Field(description="Lattice parameter c in Angstroms.", gt=0.1, le=1000.0),
    ],
    alpha: Annotated[
        float,
        Field(description="Lattice angle alpha in degrees.", gt=0.0, lt=180.0),
    ] = 90.0,
    beta: Annotated[
        float,
        Field(description="Lattice angle beta in degrees.", gt=0.0, lt=180.0),
    ] = 90.0,
    gamma: Annotated[
        float,
        Field(description="Lattice angle gamma in degrees.", gt=0.0, lt=180.0),
    ] = 90.0,
    fractional_atoms: Annotated[
        list[CrystalAtom] | None,
        Field(description="List of atoms with fractional coordinates (element, u, v, w)."),
    ] = None,
    space_group: Annotated[
        str | None,
        Field(description="Optional Hermann-Mauguin space group (e.g. 'F m -3 m', 'P 63/m m c', 'P 21/c').", max_length=50),
    ] = None,
    name: Annotated[
        str,
        Field(description="Crystal structure document name.", min_length=1, max_length=120),
    ] = "Crystal",
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
    """Build a periodic 3D crystal structure from lattice constants and fractional coordinates."""
    params = BuildCrystalInput(
        name=name,
        output_file=output_file,
        a=a,
        b=b,
        c=c,
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        fractional_atoms=fractional_atoms or [],
        space_group=space_group,
        working_dir=working_dir,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
    )
    script = build_crystal_script(
        name=params.name,
        output_file=params.output_file,
        a=params.a,
        b=params.b,
        c=params.c,
        alpha=params.alpha,
        beta=params.beta,
        gamma=params.gamma,
        fractional_atoms=[atom.model_dump() for atom in params.fractional_atoms],
        space_group=params.space_group,
    )
    if params.dry_run:
        return _dry_run(script)
    try:
        result = runner.run_script(
            script,
            working_dir=params.working_dir,
            timeout_seconds=params.timeout_seconds,
            job_prefix="build_crystal",
        )
        return _ok({"result": result.to_dict()})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="material_studio_build_supercell",
    annotations={
        "title": "Build a crystal supercell",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_build_supercell(
    source_file: Annotated[
        str,
        Field(description="Source crystal structure file (e.g. .xsd, .cif).", min_length=1, max_length=500),
    ],
    output_file: Annotated[
        str,
        Field(description="Output .xsd path for the generated supercell.", min_length=1, max_length=500),
    ],
    u: Annotated[
        int,
        Field(description="Supercell multiple along A lattice vector.", ge=1, le=50),
    ] = 1,
    v: Annotated[
        int,
        Field(description="Supercell multiple along B lattice vector.", ge=1, le=50),
    ] = 1,
    w: Annotated[
        int,
        Field(description="Supercell multiple along C lattice vector.", ge=1, le=50),
    ] = 1,
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
    """Expand an existing periodic unit cell into a supercell (e.g. 2x2x2, 3x3x1)."""
    params = BuildSupercellInput(
        source_file=source_file,
        output_file=output_file,
        u=u,
        v=v,
        w=w,
        working_dir=working_dir,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
    )
    warnings = _path_warning(params.source_file, "Source file")
    script = build_supercell_script(
        params.source_file,
        params.output_file,
        params.u,
        params.v,
        params.w,
    )
    if params.dry_run:
        return _dry_run(script, {"warnings": warnings} if warnings else None)
    try:
        result = runner.run_script(
            script,
            working_dir=params.working_dir,
            timeout_seconds=params.timeout_seconds,
            job_prefix="build_supercell",
        )
        return _ok({"result": result.to_dict()})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="material_studio_build_surface_slab",
    annotations={
        "title": "Cleave a surface slab with vacuum",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_build_surface_slab(
    source_file: Annotated[
        str,
        Field(description="Source 3D crystal structure file (e.g. .xsd, .cif).", min_length=1, max_length=500),
    ],
    output_file: Annotated[
        str,
        Field(description="Output surface/slab .xsd path.", min_length=1, max_length=500),
    ],
    h: Annotated[
        int,
        Field(description="Miller index h of the cleave plane."),
    ],
    k: Annotated[
        int,
        Field(description="Miller index k of the cleave plane."),
    ],
    l: Annotated[
        int,
        Field(description="Miller index l of the cleave plane."),
    ],
    thickness_angstrom: Annotated[
        float,
        Field(description="Slab thickness in Angstroms.", gt=0.1, le=500.0),
    ] = 10.0,
    vacuum_angstrom: Annotated[
        float,
        Field(description="Vacuum buffer thickness in Angstroms (0 for 2D slab).", ge=0.0, le=500.0),
    ] = 15.0,
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
    """Cleave a crystal surface along Miller indices (h, k, l) and construct a vacuum slab."""
    params = BuildSurfaceSlabInput(
        source_file=source_file,
        output_file=output_file,
        h=h,
        k=k,
        l=l,
        thickness_angstrom=thickness_angstrom,
        vacuum_angstrom=vacuum_angstrom,
        working_dir=working_dir,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
    )
    warnings = _path_warning(params.source_file, "Source file")
    script = build_surface_slab_script(
        params.source_file,
        params.output_file,
        params.h,
        params.k,
        params.l,
        thickness_angstrom=params.thickness_angstrom,
        vacuum_angstrom=params.vacuum_angstrom,
    )
    if params.dry_run:
        return _dry_run(script, {"warnings": warnings} if warnings else None)
    try:
        result = runner.run_script(
            script,
            working_dir=params.working_dir,
            timeout_seconds=params.timeout_seconds,
            job_prefix="build_surface_slab",
        )
        return _ok({"result": result.to_dict()})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="material_studio_forcite_dynamics",
    annotations={
        "title": "Run Forcite Molecular Dynamics",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_forcite_dynamics(
    input_file: Annotated[
        str,
        Field(description="Structure file imported into Materials Studio.", min_length=1, max_length=500),
    ],
    output_file: Annotated[
        str | None,
        Field(description="Optional trajectory/final structure output .xsd path.", max_length=500),
    ] = None,
    ensemble: Annotated[
        ForciteEnsemble,
        Field(description="Thermodynamic ensemble (NVT, NPT, NVE, NPH)."),
    ] = ForciteEnsemble.NVT,
    temperature_k: Annotated[
        float,
        Field(description="Simulation temperature in Kelvin.", gt=0.0, le=10000.0),
    ] = 298.0,
    pressure_gpa: Annotated[
        float | None,
        Field(description="Pressure in GPa (for NPT/NPH ensembles).", ge=0.0, le=1000.0),
    ] = None,
    time_step_fs: Annotated[
        float,
        Field(description="Time step in femtoseconds.", gt=0.01, le=10.0),
    ] = 1.0,
    number_of_steps: Annotated[
        int,
        Field(description="Total integration steps (total_time = steps * time_step).", ge=10, le=100_000_000),
    ] = 5000,
    thermostat: Annotated[
        str,
        Field(description="Thermostat algorithm (Nose-Hoover, Berendsen, Andersen).", max_length=50),
    ] = "Nose-Hoover",
    forcefield: Annotated[
        str,
        Field(description="Forcefield name (e.g. COMPASS, Universal, Dreiding, cvff).", min_length=1, max_length=100),
    ] = "COMPASS",
    quality: Annotated[
        ForciteQuality,
        Field(description="Forcite calculation quality setting."),
    ] = ForciteQuality.MEDIUM,
    num_cores: Annotated[
        int | None,
        Field(description="Parallel cores to allocate (-np).", ge=1, le=256),
    ] = None,
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
    """Run a Forcite Classical Molecular Dynamics simulation."""
    params = ForciteDynamicsInput(
        input_file=input_file,
        output_file=output_file,
        ensemble=ensemble,
        temperature_k=temperature_k,
        pressure_gpa=pressure_gpa,
        time_step_fs=time_step_fs,
        number_of_steps=number_of_steps,
        thermostat=thermostat,
        forcefield=forcefield,
        quality=quality,
        num_cores=num_cores,
        working_dir=working_dir,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
    )
    warnings = _path_warning(params.input_file, "Input file")
    script = forcite_dynamics_script(
        params.input_file,
        params.output_file,
        ensemble=params.ensemble.value if hasattr(params.ensemble, "value") else str(params.ensemble),
        temperature_k=params.temperature_k,
        pressure_gpa=params.pressure_gpa,
        time_step_fs=params.time_step_fs,
        number_of_steps=params.number_of_steps,
        thermostat=params.thermostat,
        forcefield=params.forcefield,
        quality=params.quality.value if hasattr(params.quality, "value") else str(params.quality),
    )
    if params.dry_run:
        return _dry_run(script, {"warnings": warnings} if warnings else None)
    try:
        result = runner.run_script(
            script,
            working_dir=params.working_dir,
            timeout_seconds=params.timeout_seconds,
            num_cores=params.num_cores,
            job_prefix="forcite_dynamics",
        )
        return _ok({"result": result.to_dict()})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="material_studio_castep_calculate",
    annotations={
        "title": "Execute CASTEP DFT calculation",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_castep_calculate(
    input_file: Annotated[
        str,
        Field(description="Structure file imported into CASTEP (e.g. .xsd, .cell, .cif).", min_length=1, max_length=500),
    ],
    output_file: Annotated[
        str | None,
        Field(description="Optional output file path for calculated/relaxed structure.", max_length=500),
    ] = None,
    task: Annotated[
        CastepTask,
        Field(description="CASTEP task: Energy, GeometryOptimization, BandStructure."),
    ] = CastepTask.ENERGY,
    quality: Annotated[
        CastepQuality,
        Field(description="CASTEP calculation quality setting."),
    ] = CastepQuality.MEDIUM,
    functional: Annotated[
        str,
        Field(description="Exchange-correlation functional (PBE, LDA, PW91, RPBE, WC, PBEsol).", min_length=1, max_length=100),
    ] = "PBE",
    cutoff_energy_ev: Annotated[
        int | None,
        Field(description="Optional plane-wave cutoff energy in eV.", ge=1, le=100_000),
    ] = None,
    kpoint_separation: Annotated[
        float | None,
        Field(description="Optional k-point grid separation (1/Angstrom).", gt=0.0, le=10.0),
    ] = None,
    max_iterations: Annotated[
        int,
        Field(description="Maximum SCF or geometry optimization iterations.", ge=1, le=2000),
    ] = 50,
    num_cores: Annotated[
        int | None,
        Field(description="Parallel cores to allocate (-np).", ge=1, le=256),
    ] = None,
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
    """Execute a CASTEP First-Principles DFT calculation (Energy, GeometryOptimization, BandStructure)."""
    params = CastepCalculateInput(
        input_file=input_file,
        output_file=output_file,
        task=task,
        quality=quality,
        functional=functional,
        cutoff_energy_ev=cutoff_energy_ev,
        kpoint_separation=kpoint_separation,
        max_iterations=max_iterations,
        num_cores=num_cores,
        working_dir=working_dir,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
    )
    warnings = _path_warning(params.input_file, "Input file")
    task_str = params.task.value if hasattr(params.task, "value") else str(params.task)
    quality_str = params.quality.value if hasattr(params.quality, "value") else str(params.quality)
    script = castep_calculate_script(
        params.input_file,
        params.output_file,
        task=task_str,
        quality=quality_str,
        functional=params.functional,
        cutoff_energy_ev=params.cutoff_energy_ev,
        kpoint_separation=params.kpoint_separation,
        max_iterations=params.max_iterations,
    )
    if params.dry_run:
        return _dry_run(script, {"warnings": warnings} if warnings else None)
    try:
        result = runner.run_script(
            script,
            working_dir=params.working_dir,
            timeout_seconds=params.timeout_seconds,
            num_cores=params.num_cores,
            job_prefix=f"castep_{task_str.lower()}",
        )
        return _ok({"result": result.to_dict()})
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    name="material_studio_reflex_powder_diffraction",
    annotations={
        "title": "Reflex XRD Powder Diffraction simulation",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
def material_studio_reflex_powder_diffraction(
    source_file: Annotated[
        str,
        Field(description="Crystal structure file (e.g. .xsd, .cif).", min_length=1, max_length=500),
    ],
    output_file: Annotated[
        str | None,
        Field(description="Optional reflections table export path (.std, .txt).", max_length=500),
    ] = None,
    two_theta_min: Annotated[
        float,
        Field(description="Minimum 2-theta angle in degrees.", ge=0.0, lt=180.0),
    ] = 5.0,
    two_theta_max: Annotated[
        float,
        Field(description="Maximum 2-theta angle in degrees.", gt=0.0, le=180.0),
    ] = 60.0,
    step_size: Annotated[
        float,
        Field(description="2-theta step size in degrees.", gt=0.0001, le=5.0),
    ] = 0.02,
    radiation: Annotated[
        str,
        Field(description="X-ray radiation source ('Cu Ka', 'Mo Ka', 'Fe Ka', etc.).", max_length=50),
    ] = "Cu Ka",
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
    """Simulate X-ray Powder Diffraction (XRD) using Reflex module."""
    params = ReflexPowderDiffractionInput(
        source_file=source_file,
        output_file=output_file,
        two_theta_min=two_theta_min,
        two_theta_max=two_theta_max,
        step_size=step_size,
        radiation=radiation,
        working_dir=working_dir,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
    )
    warnings = _path_warning(params.source_file, "Source file")
    script = reflex_powder_diffraction_script(
        params.source_file,
        params.output_file,
        two_theta_min=params.two_theta_min,
        two_theta_max=params.two_theta_max,
        step_size=params.step_size,
        radiation=params.radiation,
    )
    if params.dry_run:
        return _dry_run(script, {"warnings": warnings} if warnings else None)
    try:
        result = runner.run_script(
            script,
            working_dir=params.working_dir,
            timeout_seconds=params.timeout_seconds,
            job_prefix="reflex_xrd",
        )
        return _ok({"result": result.to_dict()})
    except Exception as exc:
        return _error(exc)


def main() -> None:
    """Run the Materials Studio MCP server over stdio."""

    mcp.run()


if __name__ == "__main__":
    main()
