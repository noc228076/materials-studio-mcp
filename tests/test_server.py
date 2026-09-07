from material_studio_mcp_server.server import MoleculeAtom, MoleculeBond, _validate_molecule_graph


def test_validate_molecule_graph_accepts_known_atoms() -> None:
    atoms = [
        MoleculeAtom(id="C1", element="C", x=0.0, y=0.0, z=0.0),
        MoleculeAtom(id="H1", element="H", x=1.0, y=0.0, z=0.0),
    ]
    bonds = [MoleculeBond(atom1="C1", atom2="H1", type="Single")]

    _validate_molecule_graph(atoms, bonds)


def test_validate_molecule_graph_rejects_unknown_atoms() -> None:
    atoms = [MoleculeAtom(id="C1", element="C", x=0.0, y=0.0, z=0.0)]
    bonds = [MoleculeBond(atom1="C1", atom2="H1", type="Single")]

    try:
        _validate_molecule_graph(atoms, bonds)
    except ValueError as exc:
        assert "H1" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_list_molecule_templates_tool() -> None:
    from material_studio_mcp_server.server import material_studio_list_molecule_templates
    res = material_studio_list_molecule_templates()
    assert res["ok"] is True
    assert any(t["id"] == "water" for t in res["templates"])
    assert any(t["id"] == "tnt" for t in res["templates"])


def test_build_molecule_with_template_dry_run() -> None:
    from material_studio_mcp_server.server import material_studio_build_molecule
    res = material_studio_build_molecule(output_file="water.xsd", template="water", dry_run=True)
    assert res["ok"] is True
    assert res["dry_run"] is True
    assert "CreateAtom('O'" in res["script"]
    assert "CreateAtom('H'" in res["script"]


def test_build_tnt_dry_run() -> None:
    from material_studio_mcp_server.server import material_studio_build_tnt
    res = material_studio_build_tnt(output_file="tnt.xsd", dry_run=True)
    assert res["ok"] is True
    assert res["dry_run"] is True
    assert "TNT_246_trinitrotoluene" in res["script"]
    assert "CreateAtom('C'" in res["script"]
    assert "CreateAtom('N'" in res["script"]


def test_build_crystal_dry_run() -> None:
    from material_studio_mcp_server.server import CrystalAtom, material_studio_build_crystal
    res = material_studio_build_crystal(
        output_file="ti.xsd",
        a=4.59,
        b=4.59,
        c=2.96,
        fractional_atoms=[CrystalAtom(element="Ti", u=0.0, v=0.0, w=0.0)],
        space_group="P 42/m n m",
        dry_run=True,
    )
    assert res["ok"] is True
    assert res["dry_run"] is True
    assert "LengthA = 4.59;" in res["script"]
    assert "'P 42/m n m'" in res["script"]


def test_build_supercell_dry_run() -> None:
    from material_studio_mcp_server.server import material_studio_build_supercell
    res = material_studio_build_supercell(source_file="bulk.xsd", output_file="super.xsd", u=2, v=2, w=2, dry_run=True)
    assert res["ok"] is True
    assert res["dry_run"] is True
    assert "BuildSuperCell(2, 2, 2);" in res["script"]


def test_build_surface_slab_dry_run() -> None:
    from material_studio_mcp_server.server import material_studio_build_surface_slab
    res = material_studio_build_surface_slab(
        source_file="bulk.xsd",
        output_file="slab.xsd",
        h=1,
        k=1,
        l=0,
        thickness_angstrom=15.0,
        vacuum_angstrom=20.0,
        dry_run=True,
    )
    assert res["ok"] is True
    assert res["dry_run"] is True
    assert "DefineCleave" in res["script"]
    assert "VacuumThickness => 20" in res["script"]


def test_forcite_dynamics_dry_run() -> None:
    from material_studio_mcp_server.server import ForciteEnsemble, material_studio_forcite_dynamics
    res = material_studio_forcite_dynamics(
        input_file="bulk.xsd",
        ensemble=ForciteEnsemble.NVT,
        temperature_k=350.0,
        dry_run=True,
    )
    assert res["ok"] is True
    assert res["dry_run"] is True
    assert "Ensemble => 'NVT'" in res["script"]
    assert "Temperature => 350.0" in res["script"]


def test_castep_calculate_dry_run() -> None:
    from material_studio_mcp_server.server import CastepTask, material_studio_castep_calculate
    res = material_studio_castep_calculate(
        input_file="bulk.xsd",
        task=CastepTask.ENERGY,
        cutoff_energy_ev=500,
        dry_run=True,
    )
    assert res["ok"] is True
    assert res["dry_run"] is True
    assert "CutoffEnergy => 500" in res["script"]
    assert "XCFunctional => 'PBE'" in res["script"]


def test_reflex_powder_diffraction_dry_run() -> None:
    from material_studio_mcp_server.server import material_studio_reflex_powder_diffraction
    res = material_studio_reflex_powder_diffraction(
        source_file="bulk.xsd",
        two_theta_min=10.0,
        two_theta_max=90.0,
        dry_run=True,
    )
    assert res["ok"] is True
    assert res["dry_run"] is True
    assert "TwoThetaMin => 10" in res["script"]
    assert "TwoThetaMax => 90" in res["script"]


def test_search_builtin_structures() -> None:
    from material_studio_mcp_server.server import material_studio_search_builtin_structures
    res = material_studio_search_builtin_structures("Si")
    # If MS Structures dir exists on this machine, it returns ok: True and matches list
    # If not on machine, it returns ok: False with clean error message
    if res["ok"]:
        assert isinstance(res["matches"], list)
    else:
        assert "not found" in res["error"]


def test_load_builtin_structure_dry_run(tmp_path) -> None:
    from material_studio_mcp_server.server import material_studio_load_builtin_structure
    dummy = tmp_path / "dummy.msi"
    dummy.write_text("dummy")
    out = tmp_path / "out.xsd"
    res = material_studio_load_builtin_structure(str(dummy), str(out), convert_to_xsd=True, dry_run=True)
    assert res["ok"] is True
    assert res["dry_run"] is True
    assert "Import" in res["script"]


