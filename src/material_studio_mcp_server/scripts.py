"""MaterialsScript Perl templates used by MCP tools."""

from __future__ import annotations

from pathlib import Path

from typing import Any

from .runner import JSON_BEGIN, JSON_END, perl_string


SCRIPT_HEADER = """#!perl
use strict;
use warnings;
use Getopt::Long;
use MaterialsScript qw(:all);

"""

from .templates import MOLECULE_TEMPLATES, get_molecule_template, list_molecule_templates


def validate_materialscript(script: str) -> dict[str, object]:
    """Perform lightweight validation for MaterialsScript Perl content."""

    warnings: list[str] = []
    errors: list[str] = []
    if "use MaterialsScript" not in script:
        errors.append("Script does not import MaterialsScript. Add: use MaterialsScript qw(:all);")
    if "use strict" not in script:
        warnings.append("Consider adding 'use strict;' for safer Perl execution.")
    if "Documents->Import" not in script and "$Documents{" not in script and "Documents->New" not in script:
        warnings.append("No document import/new operation was detected.")
    if "RunMatserver" in script or "RunMatScript" in script:
        warnings.append("Script appears to include a runner command; pass only Perl code to this MCP tool.")
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def import_export_script(source_file: str | Path, output_file: str | Path) -> str:
    """Create a script that imports one document and exports it."""

    return (
        SCRIPT_HEADER
        + _json_escape_sub()
        + f"""my $source = {perl_string(source_file)};
my $output = {perl_string(output_file)};
my $doc = Documents->Import($source);
$doc->Export($output);
print "{JSON_BEGIN}\\n";
print "{{";
print "\\\"source\\\":\\\"" . json_escape($source) . "\\\",";
print "\\\"output\\\":\\\"" . json_escape($output) . "\\\",";
print "\\\"document_name\\\":\\\"" . json_escape($doc->Name) . "\\\"";
print "}}\\n";
print "{JSON_END}\\n";
"""
    )


def structure_summary_script(source_file: str | Path) -> str:
    """Create a script that imports a structure and reports detailed crystal/molecular metadata."""

    return (
        SCRIPT_HEADER
        + _json_escape_sub()
        + f"""my $source = {perl_string(source_file)};
my $doc = Documents->Import($source);
my $atom_count = 0;
my $bond_count = 0;
my $formula = "";
my $is_periodic = 0;
my $cell_a = 0.0; my $cell_b = 0.0; my $cell_c = 0.0;
my $alpha = 0.0; my $beta = 0.0; my $gamma = 0.0;
my $cell_volume = 0.0;
my $density = 0.0;
my $space_group = "";

eval {{
    my $atoms = $doc->UnitCell->Atoms;
    foreach my $atom (@$atoms) {{ $atom_count++; }}
    $is_periodic = 1 if $atom_count > 0;
}};
if ($atom_count == 0) {{
    eval {{
        my $atoms = $doc->Atoms;
        foreach my $atom (@$atoms) {{ $atom_count++; }}
    }};
}}

eval {{
    my $bonds = $doc->Bonds;
    foreach my $bond (@$bonds) {{ $bond_count++; }}
}};

eval {{
    $formula = $doc->ChemicalFormula;
}};

if ($is_periodic) {{
    eval {{
        $cell_a = $doc->Lattice3D->LengthA;
        $cell_b = $doc->Lattice3D->LengthB;
        $cell_c = $doc->Lattice3D->LengthC;
        $alpha  = $doc->Lattice3D->AngleAlpha;
        $beta   = $doc->Lattice3D->AngleBeta;
        $gamma  = $doc->Lattice3D->AngleGamma;
        $cell_volume = $doc->Lattice3D->CellVolume;
    }};
    eval {{
        $density = $doc->Density;
    }};
    eval {{
        $space_group = $doc->SymmetrySystem->SpaceGroup->Name;
    }};
    if (!$space_group) {{
        eval {{ $space_group = $doc->SymmetrySystem->SpaceGroup->GroupName; }};
    }}
}}

print "{JSON_BEGIN}\\n";
print "{{";
print "\\\"source\\\":\\\"" . json_escape($source) . "\\\",";
print "\\\"document_name\\\":\\\"" . json_escape($doc->Name) . "\\\",";
print "\\\"atom_count\\\":$atom_count,";
print "\\\"bond_count\\\":$bond_count,";
print "\\\"formula\\\":\\\"" . json_escape($formula) . "\\\",";
print "\\\"is_periodic\\\":" . ($is_periodic ? "true" : "false") . ",";
print "\\\"cell_a\\\":$cell_a,";
print "\\\"cell_b\\\":$cell_b,";
print "\\\"cell_c\\\":$cell_c,";
print "\\\"alpha\\\":$alpha,";
print "\\\"beta\\\":$beta,";
print "\\\"gamma\\\":$gamma,";
print "\\\"cell_volume\\\":$cell_volume,";
print "\\\"density\\\":$density,";
print "\\\"space_group\\\":\\\"" . json_escape($space_group) . "\\\"";
print "}}\\n";
print "{JSON_END}\\n";
"""
    )


def forcite_geometry_optimization_script(
    input_file: str | Path,
    output_file: str | Path | None,
    *,
    forcefield: str,
    quality: str,
    charge_assignment: str,
    max_iterations: int,
    convergence: str,
) -> str:
    """Create a Forcite geometry optimization script."""

    export_line = ""
    if output_file:
        export_line = f"$doc->Export({perl_string(output_file)});\n"

    return (
        SCRIPT_HEADER
        + _json_escape_sub()
        + f"""my $input = {perl_string(input_file)};
my $doc = Documents->Import($input);

Modules->Forcite->ChangeSettings([
    CurrentForcefield => {perl_string(forcefield)},
    Quality => {perl_string(quality)},
    AssignForcefieldTypes => "Yes",
    AssignChargeGroups => "Yes",
    ChargeAssignment => {perl_string(charge_assignment)},
    MaxIterations => {max_iterations},
    Convergence => {perl_string(convergence)}
]);

my $results = Modules->Forcite->GeometryOptimization->Run($doc);
{export_line}print "{JSON_BEGIN}\\n";
print "{{";
print "\\\"input\\\":\\\"" . json_escape($input) . "\\\",";
print "\\\"output\\\":\\\"" . json_escape({perl_string(output_file or "")}) . "\\\",";
print "\\\"document_name\\\":\\\"" . json_escape($doc->Name) . "\\\",";
print "\\\"forcefield\\\":\\\"" . json_escape({perl_string(forcefield)}) . "\\\",";
print "\\\"quality\\\":\\\"" . json_escape({perl_string(quality)}) . "\\\"";
print "}}\\n";
print "{JSON_END}\\n";
"""
    )


def build_molecule_script(
    name: str,
    output_file: str | Path,
    atoms: list[dict[str, object]],
    bonds: list[dict[str, str]],
    *,
    optimize: bool,
    forcefield: str | None,
    quality: str | None,
    max_iterations: int | None,
) -> str:
    """Create a MaterialsScript script that builds a molecule using the MS API."""

    atom_lines: list[str] = []
    for atom in atoms:
        atom_id = str(atom["id"])
        element = str(atom["element"])
        x = float(atom["x"])
        y = float(atom["y"])
        z = float(atom["z"])
        atom_lines.append(
            f"$atoms{{{perl_string(atom_id)}}} = $doc->CreateAtom({perl_string(element)}, "
            f"Point(X => {x:.8g}, Y => {y:.8g}, Z => {z:.8g}));"
        )

    bond_lines: list[str] = []
    for bond in bonds:
        atom1 = str(bond["atom1"])
        atom2 = str(bond["atom2"])
        bond_type = str(bond["type"])
        bond_lines.append(
            f"$doc->CreateBond($atoms{{{perl_string(atom1)}}}, $atoms{{{perl_string(atom2)}}}, {perl_string(bond_type)});"
        )

    optimize_block = "my $optimization_ok = 0;\nmy $optimization_error = \"\";\n"
    if optimize:
        settings_lines: list[str] = []
        if forcefield:
            settings_lines.append(f"    CurrentForcefield => {perl_string(forcefield)}")
        if quality:
            settings_lines.append(f"    Quality => {perl_string(quality)}")
        if max_iterations is not None:
            settings_lines.append(f"    MaxIterations => {max_iterations}")
        settings_block = ""
        if settings_lines:
            settings_block = "    Modules->Forcite->ChangeSettings([\n" + ",\n".join(settings_lines) + "\n    ]);\n"
        optimize_block += f"""eval {{
{settings_block}    Modules->Forcite->GeometryOptimization->Run($doc);
    $optimization_ok = 1;
}};
if ($@) {{
    $optimization_error = $@;
}}
"""

    atom_count = len(atoms)
    bond_count = len(bonds)
    return (
        SCRIPT_HEADER
        + _json_escape_sub()
        + f"""my $name = {perl_string(name)};
my $output = {perl_string(output_file)};
my $doc = Documents->New($name . ".xsd");
my %atoms;

"""
        + "\n".join(atom_lines)
        + "\n\n"
        + "\n".join(bond_lines)
        + "\n\n"
        + optimize_block
        + f"""
$doc->Export($output, Settings(Version => "2020"));

print "{JSON_BEGIN}\\n";
print "{{";
print "\\\"name\\\":\\\"" . json_escape($name) . "\\\",";
print "\\\"output\\\":\\\"" . json_escape($output) . "\\\",";
print "\\\"atom_count\\\":{atom_count},";
print "\\\"bond_count\\\":{bond_count},";
print "\\\"optimized\\\":" . ($optimization_ok ? "true" : "false") . ",";
print "\\\"optimization_error\\\":\\\"" . json_escape($optimization_error) . "\\\"";
print "}}\\n";
print "{JSON_END}\\n";
"""
    )


def forcite_dynamics_script(
    input_file: str | Path,
    output_file: str | Path | None,
    *,
    ensemble: str = "NVT",
    temperature_k: float = 298.0,
    pressure_gpa: float | None = None,
    time_step_fs: float = 1.0,
    number_of_steps: int = 5000,
    thermostat: str = "Nosé",
    forcefield: str = "COMPASS",
    quality: str = "Medium",
) -> str:
    """Create a Forcite Molecular Dynamics script."""

    export_line = ""
    if output_file:
        export_line = f"$doc->Export({perl_string(output_file)}, Settings(Version => '2020'));\n"

    extra_settings: list[str] = []
    if pressure_gpa is not None and ensemble.upper() in ("NPT", "NPH"):
        extra_settings.append(f"    Pressure => {pressure_gpa}")
    joined_extra = (",\n" + ",\n".join(extra_settings)) if extra_settings else ""

    return (
        SCRIPT_HEADER
        + _json_escape_sub()
        + f"""my $input = {perl_string(input_file)};
my $doc = Documents->Import($input);

Modules->Forcite->ChangeSettings([
    CurrentForcefield => {perl_string(forcefield)},
    Quality => {perl_string(quality)},
    AssignForcefieldTypes => "Yes",
    AssignChargeGroups => "Yes"
]);

my $results = Modules->Forcite->Dynamics->Run($doc, Settings(
    Ensemble => {perl_string(ensemble)},
    Temperature => {temperature_k},
    TimeStep => {time_step_fs},
    NumberOfSteps => {number_of_steps},
    Thermostat => {perl_string(thermostat)}{joined_extra}
));

{export_line}print "{JSON_BEGIN}\\n";
print "{{";
print "\\\"input\\\":\\\"" . json_escape($input) . "\\\",";
print "\\\"output\\\":\\\"" . json_escape({perl_string(output_file or "")}) . "\\\",";
print "\\\"document_name\\\":\\\"" . json_escape($doc->Name) . "\\\",";
print "\\\"ensemble\\\":\\\"" . json_escape({perl_string(ensemble)}) . "\\\",";
print "\\\"temperature_k\\\":{temperature_k},";
print "\\\"time_step_fs\\\":{time_step_fs},";
print "\\\"number_of_steps\\\":{number_of_steps},";
print "\\\"status\\\":\\\"completed\\\"";
print "}}\\n";
print "{JSON_END}\\n";
"""
    )


def build_crystal_script(
    name: str,
    output_file: str | Path,
    a: float,
    b: float,
    c: float,
    alpha: float = 90.0,
    beta: float = 90.0,
    gamma: float = 90.0,
    fractional_atoms: list[dict[str, Any]] | None = None,
    space_group: str | None = None,
) -> str:
    """Create a MaterialsScript that builds a periodic 3D crystal structure."""

    atom_lines: list[str] = []
    for atom in (fractional_atoms or []):
        elem = str(atom["element"])
        u = float(atom.get("u", atom.get("x", 0.0)))
        v = float(atom.get("v", atom.get("y", 0.0)))
        w = float(atom.get("w", atom.get("z", 0.0)))
        atom_lines.append(
            f"$doc->CreateAtom({perl_string(elem)}, "
            f"$doc->Lattice3D->FromFractionalPosition(Point(X => {u:.8g}, Y => {v:.8g}, Z => {w:.8g})));"
        )

    sg_line = ""
    if space_group and space_group.strip() and space_group.strip().upper() not in ("P 1", "P1"):
        sg_line = f"""eval {{
    Tools->Symmetry->FindSymmetry($doc, Settings(SpaceGroupName => {perl_string(space_group)}));
}};
"""

    return (
        SCRIPT_HEADER
        + _json_escape_sub()
        + f"""my $name = {perl_string(name)};
my $output = {perl_string(output_file)};
my $doc = Documents->New($name . ".xsd");
$doc->MakeP1;
$doc->Lattice3D->LengthA = {a:.8g};
$doc->Lattice3D->LengthB = {b:.8g};
$doc->Lattice3D->LengthC = {c:.8g};
$doc->Lattice3D->AngleAlpha = {alpha:.8g};
$doc->Lattice3D->AngleBeta = {beta:.8g};
$doc->Lattice3D->AngleGamma = {gamma:.8g};

"""
        + "\n".join(atom_lines)
        + "\n\n"
        + sg_line
        + f"""$doc->Export($output, Settings(Version => "2020"));

my $atom_count = 0;
eval {{
    my $atoms = $doc->UnitCell->Atoms;
    foreach my $atom (@$atoms) {{ $atom_count++; }}
}};
my $volume = 0;
eval {{ $volume = $doc->Lattice3D->CellVolume; }};

print "{JSON_BEGIN}\\n";
print "{{";
print "\\\"name\\\":\\\"" . json_escape($name) . "\\\",";
print "\\\"output\\\":\\\"" . json_escape($output) . "\\\",";
print "\\\"atom_count\\\":$atom_count,";
print "\\\"cell_volume\\\":$volume,";
print "\\\"status\\\":\\\"created\\\"";
print "}}\\n";
print "{JSON_END}\\n";
"""
    )


def build_supercell_script(
    source_file: str | Path,
    output_file: str | Path,
    u: int,
    v: int,
    w: int,
) -> str:
    """Create a script that expands a periodic crystal into a supercell."""

    return (
        SCRIPT_HEADER
        + _json_escape_sub()
        + f"""my $source = {perl_string(source_file)};
my $output = {perl_string(output_file)};
my $doc = Documents->Import($source);
$doc->BuildSuperCell({u}, {v}, {w});
$doc->Export($output, Settings(Version => "2020"));

my $atom_count = 0;
eval {{
    my $atoms = $doc->UnitCell->Atoms;
    foreach my $atom (@$atoms) {{ $atom_count++; }}
}};
my $volume = 0;
eval {{ $volume = $doc->Lattice3D->CellVolume; }};

print "{JSON_BEGIN}\\n";
print "{{";
print "\\\"source\\\":\\\"" . json_escape($source) . "\\\",";
print "\\\"output\\\":\\\"" . json_escape($output) . "\\\",";
print "\\\"supercell\\\":[{u}, {v}, {w}],";
print "\\\"atom_count\\\":$atom_count,";
print "\\\"cell_volume\\\":$volume";
print "}}\\n";
print "{JSON_END}\\n";
"""
    )


def build_surface_slab_script(
    source_file: str | Path,
    output_file: str | Path,
    h: int,
    k: int,
    l: int,
    thickness_angstrom: float = 10.0,
    vacuum_angstrom: float = 15.0,
) -> str:
    """Create a script that cleaves a surface from a crystal and adds vacuum."""

    vacuum_block = ""
    if vacuum_angstrom > 0:
        vacuum_block = f"$surfaceDoc->BuildVacuumSlab(Settings(VacuumThickness => {vacuum_angstrom:.8g}));\n"

    return (
        SCRIPT_HEADER
        + _json_escape_sub()
        + f"""my $source = {perl_string(source_file)};
my $output = {perl_string(output_file)};
my $crystalDoc = Documents->Import($source);

Tools->SurfaceBuilder->CleaveSurface->DefineCleave($crystalDoc, {h}, {k}, {l});
Tools->SurfaceBuilder->CleaveSurface->SetThickness({thickness_angstrom:.8g}, "Angstrom");
my $surfaceDoc = Tools->SurfaceBuilder->CleaveSurface->Cleave;
{vacuum_block}$surfaceDoc->Export($output, Settings(Version => "2020"));

my $atom_count = 0;
eval {{
    my $atoms = $surfaceDoc->Atoms;
    foreach my $atom (@$atoms) {{ $atom_count++; }}
}};

print "{JSON_BEGIN}\\n";
print "{{";
print "\\\"source\\\":\\\"" . json_escape($source) . "\\\",";
print "\\\"output\\\":\\\"" . json_escape($output) . "\\\",";
print "\\\"miller_indices\\\":[{h}, {k}, {l}],";
print "\\\"thickness_angstrom\\\":{thickness_angstrom:.8g},";
print "\\\"vacuum_angstrom\\\":{vacuum_angstrom:.8g},";
print "\\\"atom_count\\\":$atom_count";
print "}}\\n";
print "{JSON_END}\\n";
"""
    )


def castep_calculate_script(
    input_file: str | Path,
    output_file: str | Path | None = None,
    *,
    task: str = "Energy",
    quality: str = "Medium",
    functional: str = "PBE",
    cutoff_energy_ev: int | None = None,
    kpoint_separation: float | None = None,
    max_iterations: int = 50,
) -> str:
    """Create an executable CASTEP calculation script."""

    export_line = ""
    if output_file:
        export_line = f"eval {{ $doc->Export({perl_string(output_file)}, Settings(Version => '2020')); }};\n"

    settings = [
        f"    Quality => {perl_string(quality)}",
        f"    Task => {perl_string(task)}",
        f"    XCFunctional => {perl_string(functional)}",
        f"    MaxIterations => {max_iterations}",
    ]
    if cutoff_energy_ev is not None:
        settings.append(f"    CutoffEnergy => {cutoff_energy_ev}")
    if kpoint_separation is not None:
        settings.append(f"    KPointSeparation => {kpoint_separation}")
    joined_settings = ",\n".join(settings)

    return (
        SCRIPT_HEADER
        + _json_escape_sub()
        + f"""my $input = {perl_string(input_file)};
my $doc = Documents->Import($input);

my $results;
my $calc_success = 0;
my $calc_error = "";

eval {{
    $results = Modules->CASTEP->{task}->Run($doc, Settings(
{joined_settings}
    ));
    $calc_success = 1;
}};
if ($@) {{
    $calc_error = $@;
}}

{export_line}print "{JSON_BEGIN}\\n";
print "{{";
print "\\\"input\\\":\\\"" . json_escape($input) . "\\\",";
print "\\\"output\\\":\\\"" . json_escape({perl_string(output_file or "")}) . "\\\",";
print "\\\"task\\\":\\\"" . json_escape({perl_string(task)}) . "\\\",";
print "\\\"functional\\\":\\\"" . json_escape({perl_string(functional)}) . "\\\",";
print "\\\"quality\\\":\\\"" . json_escape({perl_string(quality)}) . "\\\",";
print "\\\"success\\\":" . ($calc_success ? "true" : "false") . ",";
print "\\\"error\\\":\\\"" . json_escape($calc_error) . "\\\"";
print "}}\\n";
print "{JSON_END}\\n";
"""
    )


def reflex_powder_diffraction_script(
    source_file: str | Path,
    output_file: str | Path | None = None,
    *,
    two_theta_min: float = 5.0,
    two_theta_max: float = 60.0,
    step_size: float = 0.02,
    radiation: str = "Cu Ka",
) -> str:
    """Create a Reflex Powder Diffraction XRD simulation script."""

    export_line = ""
    if output_file:
        export_line = f"eval {{ $results->ReflectionsStudyTable->Export({perl_string(output_file)}); }};\n"

    return (
        SCRIPT_HEADER
        + _json_escape_sub()
        + f"""my $source = {perl_string(source_file)};
my $doc = Documents->Import($source);

Modules->Reflex->ChangeSettings(Settings(
    TwoThetaMin => {two_theta_min:.8g},
    TwoThetaMax => {two_theta_max:.8g},
    StepSize => {step_size:.8g},
    XRaySource => {perl_string(radiation)}
));

my $results = Modules->Reflex->PowderDiffraction->Run($doc, Settings(
    CreateReflectionsStudyTable => "Yes"
));

{export_line}print "{JSON_BEGIN}\\n";
print "{{";
print "\\\"source\\\":\\\"" . json_escape($source) . "\\\",";
print "\\\"two_theta_min\\\":{two_theta_min:.8g},";
print "\\\"two_theta_max\\\":{two_theta_max:.8g},";
print "\\\"step_size\\\":{step_size:.8g},";
print "\\\"radiation\\\":\\\"" . json_escape({perl_string(radiation)}) . "\\\",";
print "\\\"status\\\":\\\"completed\\\"";
print "}}\\n";
print "{JSON_END}\\n";
"""
    )


def castep_energy_script(
    input_file: str | Path,
    *,
    quality: str,
    task: str,
    functional: str,
    cutoff_energy_ev: int | None,
    kpoint_separation: float | None,
) -> str:
    """Create a CASTEP Energy script template."""

    settings = [
        f"    Quality => {perl_string(quality)}",
        f"    Task => {perl_string(task)}",
        f"    XCFunctional => {perl_string(functional)}",
    ]
    if cutoff_energy_ev is not None:
        settings.append(f"    CutoffEnergy => {cutoff_energy_ev}")
    if kpoint_separation is not None:
        settings.append(f"    KPointSeparation => {kpoint_separation}")
    joined_settings = ",\n".join(settings)

    return (
        SCRIPT_HEADER
        + f"""my $input = {perl_string(input_file)};
my $doc = Documents->Import($input);
my $results = Modules->CASTEP->Energy->Run($doc, Settings(
{joined_settings}
));
print "CASTEP Energy finished for " . $doc->Name . "\\n";
"""
    )


def template_catalog() -> list[dict[str, str]]:
    """Return built-in script templates."""

    return [
        {
            "name": "import_export",
            "tool": "material_studio_import_export",
            "description": "Import a structure file and export it to another Materials Studio-supported format.",
        },
        {
            "name": "structure_summary",
            "tool": "material_studio_structure_summary",
            "description": "Import a structure and emit full atom/lattice/volume/density metadata as tagged JSON.",
        },
        {
            "name": "build_crystal",
            "tool": "material_studio_build_crystal",
            "description": "Build a 3D periodic crystal with lattice parameters, space group, and fractional coordinates.",
        },
        {
            "name": "build_supercell",
            "tool": "material_studio_build_supercell",
            "description": "Expand a unit cell into a supercell (u, v, w) using native BuildSuperCell.",
        },
        {
            "name": "build_surface_slab",
            "tool": "material_studio_build_surface_slab",
            "description": "Cleave a crystal surface along (h, k, l) and optionally add vacuum slab thickness.",
        },
        {
            "name": "forcite_geometry_optimization",
            "tool": "material_studio_forcite_geometry_optimization",
            "description": "Run Forcite GeometryOptimization with forcefield, quality, and convergence settings.",
        },
        {
            "name": "forcite_dynamics",
            "tool": "material_studio_forcite_dynamics",
            "description": "Run Forcite Molecular Dynamics (NVT/NPT/NVE) with temperature and timestep controls.",
        },
        {
            "name": "castep_calculate",
            "tool": "material_studio_castep_calculate",
            "description": "Execute CASTEP DFT calculations (Energy, GeometryOptimization, BandStructure) directly.",
        },
        {
            "name": "reflex_powder_diffraction",
            "tool": "material_studio_reflex_powder_diffraction",
            "description": "Simulate powder XRD diffraction patterns from crystals with 2-theta ranges.",
        },
        {
            "name": "build_molecule",
            "tool": "material_studio_build_molecule",
            "description": "Build a molecular XSD using CreateAtom/CreateBond or built-in templates (water, benzene, etc.).",
        },
        {
            "name": "build_tnt",
            "tool": "material_studio_build_tnt",
            "description": "Build 2,4,6-trinitrotoluene using the built-in molecule template system.",
        },
        {
            "name": "castep_energy",
            "tool": "material_studio_castep_energy_script",
            "description": "Generate a CASTEP Energy MaterialsScript template for inspection.",
        },
    ]


def _json_escape_sub() -> str:
    return r"""sub json_escape {
    my ($value) = @_;
    $value = "" unless defined $value;
    $value =~ s/\\/\\\\/g;
    $value =~ s/"/\\"/g;
    $value =~ s/\r/\\r/g;
    $value =~ s/\n/\\n/g;
    $value =~ s/\t/\\t/g;
    return $value;
}

"""
