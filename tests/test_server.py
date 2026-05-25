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
