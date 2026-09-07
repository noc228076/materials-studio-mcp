from material_studio_mcp_server.runner import extract_tagged_json, perl_string
from material_studio_mcp_server.scripts import (
    forcite_geometry_optimization_script,
    import_export_script,
    validate_materialscript,
)


def test_extract_tagged_json() -> None:
    output = 'noise\n__MATERIAL_STUDIO_MCP_JSON_BEGIN__\n{"ok": true}\n__MATERIAL_STUDIO_MCP_JSON_END__\n'
    assert extract_tagged_json(output) == {"ok": True}


def test_perl_string_escapes_backslash_and_quote() -> None:
    assert perl_string(r"C:\a\b's.xsd") == r"'C:\\a\\b\'s.xsd'"


def test_import_export_script_uses_materialscript() -> None:
    script = import_export_script(r"C:\in.cif", r"C:\out.xsd")
    assert "use MaterialsScript qw(:all);" in script
    assert "Documents->Import" in script
    assert "$doc->Export" in script


def test_forcite_script_contains_expected_task() -> None:
    script = forcite_geometry_optimization_script(
        r"C:\in.xsd",
        r"C:\out.xsd",
        forcefield="COMPASS",
        quality="Medium",
        charge_assignment="Forcefield assigned",
        max_iterations=500,
        convergence="Medium",
    )
    assert "Modules->Forcite->GeometryOptimization->Run($doc)" in script
    assert "CurrentForcefield => 'COMPASS'" in script


def test_validate_materialscript_requires_import() -> None:
    result = validate_materialscript("print 'hello';")
    assert result["valid"] is False
    assert result["errors"]


def test_molecule_templates() -> None:
    from material_studio_mcp_server.scripts import get_molecule_template, list_molecule_templates
    templates = list_molecule_templates()
    ids = [t["id"] for t in templates]
    assert "water" in ids
    assert "benzene" in ids
    assert "tnt" in ids

    water = get_molecule_template("water")
    assert water is not None
    assert len(water["atoms"]) == 3
    assert len(water["bonds"]) == 2

    tnt = get_molecule_template("tnt")
    assert tnt is not None
    assert len(tnt["atoms"]) == 21
    assert len(tnt["bonds"]) == 21


def test_build_crystal_script() -> None:
    from material_studio_mcp_server.scripts import build_crystal_script
    atoms = [{"element": "Si", "u": 0.0, "v": 0.0, "w": 0.0}]
    script = build_crystal_script("Silicon", "silicon.xsd", 5.43, 5.43, 5.43, 90, 90, 90, atoms, "F d -3 m")
    assert "$doc->Lattice3D->LengthA = 5.43;" in script
    assert "FromFractionalPosition" in script
    assert "Tools->Symmetry->FindSymmetry" in script
    assert "'F d -3 m'" in script


def test_build_supercell_script() -> None:
    from material_studio_mcp_server.scripts import build_supercell_script
    script = build_supercell_script("unit.xsd", "super.xsd", 2, 3, 4)
    assert "$doc->BuildSuperCell(2, 3, 4);" in script
    assert "$doc->Export" in script


def test_build_surface_slab_script() -> None:
    from material_studio_mcp_server.scripts import build_surface_slab_script
    script = build_surface_slab_script("bulk.xsd", "slab.xsd", 1, 1, 1, thickness_angstrom=12.5, vacuum_angstrom=15.0)
    assert "DefineCleave($crystalDoc, 1, 1, 1)" in script
    assert "SetThickness(12.5, \"Angstrom\")" in script
    assert "BuildVacuumSlab(Settings(VacuumThickness => 15))" in script


def test_forcite_dynamics_script() -> None:
    from material_studio_mcp_server.scripts import forcite_dynamics_script
    script = forcite_dynamics_script(
        "in.xsd",
        "out.xsd",
        ensemble="NPT",
        temperature_k=300.0,
        pressure_gpa=0.0001,
        time_step_fs=1.0,
        number_of_steps=1000,
    )
    assert "Modules->Forcite->Dynamics->Run" in script
    assert "Ensemble => 'NPT'" in script
    assert "Pressure => 0.0001" in script
    assert "Temperature => 300.0" in script


def test_castep_calculate_script() -> None:
    from material_studio_mcp_server.scripts import castep_calculate_script
    script = castep_calculate_script(
        "in.xsd",
        "out.xsd",
        task="GeometryOptimization",
        quality="Fine",
        functional="PBE",
        cutoff_energy_ev=400,
        kpoint_separation=0.04,
    )
    assert "Modules->CASTEP->GeometryOptimization->Run" in script
    assert "Quality => 'Fine'" in script
    assert "XCFunctional => 'PBE'" in script
    assert "CutoffEnergy => 400" in script


def test_reflex_powder_diffraction_script() -> None:
    from material_studio_mcp_server.scripts import reflex_powder_diffraction_script
    script = reflex_powder_diffraction_script("in.xsd", "pattern.std", two_theta_min=10.0, two_theta_max=80.0, radiation="Cu Ka")
    assert "Modules->Reflex->PowderDiffraction->Run" in script
    assert "TwoThetaMin => 10" in script
    assert "TwoThetaMax => 80" in script
    assert "XRaySource => 'Cu Ka'" in script

