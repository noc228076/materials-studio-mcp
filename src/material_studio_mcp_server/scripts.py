"""MaterialsScript Perl templates used by MCP tools."""

from __future__ import annotations

from pathlib import Path

from .runner import JSON_BEGIN, JSON_END, perl_string


SCRIPT_HEADER = """#!perl
use strict;
use warnings;
use Getopt::Long;
use MaterialsScript qw(:all);

"""


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
    """Create a script that imports a structure and reports basic counts."""

    return (
        SCRIPT_HEADER
        + _json_escape_sub()
        + f"""my $source = {perl_string(source_file)};
my $doc = Documents->Import($source);
my $atom_count = 0;
my $bond_count = 0;
my $formula = "";

eval {{
    my $atoms = $doc->UnitCell->Atoms;
    foreach my $atom (@$atoms) {{ $atom_count++; }}
}};
if ($@ || $atom_count == 0) {{
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

print "{JSON_BEGIN}\\n";
print "{{";
print "\\\"source\\\":\\\"" . json_escape($source) . "\\\",";
print "\\\"document_name\\\":\\\"" . json_escape($doc->Name) . "\\\",";
print "\\\"atom_count\\\":$atom_count,";
print "\\\"bond_count\\\":$bond_count,";
print "\\\"formula\\\":\\\"" . json_escape($formula) . "\\\"";
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
            "description": "Import a structure and emit basic atom/bond/formula metadata as tagged JSON.",
        },
        {
            "name": "forcite_geometry_optimization",
            "tool": "material_studio_forcite_geometry_optimization",
            "description": "Run Forcite GeometryOptimization with forcefield, quality, and convergence settings.",
        },
        {
            "name": "build_molecule",
            "tool": "material_studio_build_molecule",
            "description": "Build a molecular XSD with MaterialsScript CreateAtom/CreateBond instead of hand-writing XML.",
        },
        {
            "name": "build_tnt",
            "tool": "material_studio_build_tnt",
            "description": "Build 2,4,6-trinitrotoluene using a built-in atom/bond template.",
        },
        {
            "name": "castep_energy",
            "tool": "material_studio_castep_energy_script",
            "description": "Generate a CASTEP Energy MaterialsScript template for licensed CASTEP installations.",
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
