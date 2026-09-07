"""Predefined molecular templates and catalogs for Materials Studio."""

from __future__ import annotations

from typing import Any


MOLECULE_TEMPLATES: dict[str, dict[str, Any]] = {
    "water": {
        "name": "Water",
        "formula": "H2O",
        "description": "Water molecule with standard gas-phase geometry (r_OH=0.9584 A, angle=104.45 deg)",
        "atoms": [
            {"id": "O1", "element": "O", "x": 0.000, "y": 0.000, "z": 0.117},
            {"id": "H1", "element": "H", "x": 0.000, "y": 0.757, "z": -0.469},
            {"id": "H2", "element": "H", "x": 0.000, "y": -0.757, "z": -0.469},
        ],
        "bonds": [
            {"atom1": "O1", "atom2": "H1", "type": "Single"},
            {"atom1": "O1", "atom2": "H2", "type": "Single"},
        ],
    },
    "methane": {
        "name": "Methane",
        "formula": "CH4",
        "description": "Methane molecule with tetrahedral geometry (r_CH=1.087 A)",
        "atoms": [
            {"id": "C1", "element": "C", "x": 0.000, "y": 0.000, "z": 0.000},
            {"id": "H1", "element": "H", "x": 0.628, "y": 0.628, "z": 0.628},
            {"id": "H2", "element": "H", "x": -0.628, "y": -0.628, "z": 0.628},
            {"id": "H3", "element": "H", "x": -0.628, "y": 0.628, "z": -0.628},
            {"id": "H4", "element": "H", "x": 0.628, "y": -0.628, "z": -0.628},
        ],
        "bonds": [
            {"atom1": "C1", "atom2": "H1", "type": "Single"},
            {"atom1": "C1", "atom2": "H2", "type": "Single"},
            {"atom1": "C1", "atom2": "H3", "type": "Single"},
            {"atom1": "C1", "atom2": "H4", "type": "Single"},
        ],
    },
    "benzene": {
        "name": "Benzene",
        "formula": "C6H6",
        "description": "Planar benzene ring with alternating aromatic bonds (r_CC=1.40 A, r_CH=1.08 A)",
        "atoms": [
            {"id": "C1", "element": "C", "x": 1.400, "y": 0.000, "z": 0.000},
            {"id": "C2", "element": "C", "x": 0.700, "y": 1.212, "z": 0.000},
            {"id": "C3", "element": "C", "x": -0.700, "y": 1.212, "z": 0.000},
            {"id": "C4", "element": "C", "x": -1.400, "y": 0.000, "z": 0.000},
            {"id": "C5", "element": "C", "x": -0.700, "y": -1.212, "z": 0.000},
            {"id": "C6", "element": "C", "x": 0.700, "y": -1.212, "z": 0.000},
            {"id": "H1", "element": "H", "x": 2.480, "y": 0.000, "z": 0.000},
            {"id": "H2", "element": "H", "x": 1.240, "y": 2.148, "z": 0.000},
            {"id": "H3", "element": "H", "x": -1.240, "y": 2.148, "z": 0.000},
            {"id": "H4", "element": "H", "x": -2.480, "y": 0.000, "z": 0.000},
            {"id": "H5", "element": "H", "x": -1.240, "y": -2.148, "z": 0.000},
            {"id": "H6", "element": "H", "x": 1.240, "y": -2.148, "z": 0.000},
        ],
        "bonds": [
            {"atom1": "C1", "atom2": "C2", "type": "Aromatic"},
            {"atom1": "C2", "atom2": "C3", "type": "Aromatic"},
            {"atom1": "C3", "atom2": "C4", "type": "Aromatic"},
            {"atom1": "C4", "atom2": "C5", "type": "Aromatic"},
            {"atom1": "C5", "atom2": "C6", "type": "Aromatic"},
            {"atom1": "C6", "atom2": "C1", "type": "Aromatic"},
            {"atom1": "C1", "atom2": "H1", "type": "Single"},
            {"atom1": "C2", "atom2": "H2", "type": "Single"},
            {"atom1": "C3", "atom2": "H3", "type": "Single"},
            {"atom1": "C4", "atom2": "H4", "type": "Single"},
            {"atom1": "C5", "atom2": "H5", "type": "Single"},
            {"atom1": "C6", "atom2": "H6", "type": "Single"},
        ],
    },
    "tnt": {
        "name": "TNT_246_trinitrotoluene",
        "formula": "C7H5N3O6",
        "description": "2,4,6-trinitrotoluene (TNT) molecule for energetic material simulation",
        "atoms": [
            {"id": "C1", "element": "C", "x": 1.400, "y": 0.000, "z": 0.000},
            {"id": "C2", "element": "C", "x": 0.700, "y": 1.212, "z": 0.000},
            {"id": "C3", "element": "C", "x": -0.700, "y": 1.212, "z": 0.000},
            {"id": "C4", "element": "C", "x": -1.400, "y": 0.000, "z": 0.000},
            {"id": "C5", "element": "C", "x": -0.700, "y": -1.212, "z": 0.000},
            {"id": "C6", "element": "C", "x": 0.700, "y": -1.212, "z": 0.000},
            {"id": "C7", "element": "C", "x": 2.910, "y": 0.000, "z": 0.000},
            {"id": "H1", "element": "H", "x": 3.550, "y": 0.630, "z": 0.000},
            {"id": "H2", "element": "H", "x": 3.550, "y": -0.315, "z": 0.546},
            {"id": "H3", "element": "H", "x": 3.550, "y": -0.315, "z": -0.546},
            {"id": "H4", "element": "H", "x": -1.250, "y": 2.162, "z": 0.000},
            {"id": "H5", "element": "H", "x": -1.250, "y": -2.162, "z": 0.000},
            {"id": "N1", "element": "N", "x": 1.440, "y": 2.490, "z": 0.000},
            {"id": "O1", "element": "O", "x": 1.990, "y": 3.250, "z": 0.350},
            {"id": "O2", "element": "O", "x": 0.930, "y": 3.070, "z": -0.350},
            {"id": "N2", "element": "N", "x": -2.870, "y": 0.000, "z": 0.000},
            {"id": "O3", "element": "O", "x": -3.610, "y": -0.610, "z": 0.200},
            {"id": "O4", "element": "O", "x": -3.610, "y": 0.610, "z": -0.200},
            {"id": "N3", "element": "N", "x": 1.440, "y": -2.490, "z": 0.000},
            {"id": "O5", "element": "O", "x": 1.990, "y": -3.250, "z": -0.350},
            {"id": "O6", "element": "O", "x": 0.930, "y": -3.070, "z": 0.350},
        ],
        "bonds": [
            {"atom1": "C1", "atom2": "C2", "type": "Aromatic"},
            {"atom1": "C2", "atom2": "C3", "type": "Aromatic"},
            {"atom1": "C3", "atom2": "C4", "type": "Aromatic"},
            {"atom1": "C4", "atom2": "C5", "type": "Aromatic"},
            {"atom1": "C5", "atom2": "C6", "type": "Aromatic"},
            {"atom1": "C6", "atom2": "C1", "type": "Aromatic"},
            {"atom1": "C1", "atom2": "C7", "type": "Single"},
            {"atom1": "C7", "atom2": "H1", "type": "Single"},
            {"atom1": "C7", "atom2": "H2", "type": "Single"},
            {"atom1": "C7", "atom2": "H3", "type": "Single"},
            {"atom1": "C3", "atom2": "H4", "type": "Single"},
            {"atom1": "C5", "atom2": "H5", "type": "Single"},
            {"atom1": "C2", "atom2": "N1", "type": "Single"},
            {"atom1": "N1", "atom2": "O1", "type": "Double"},
            {"atom1": "N1", "atom2": "O2", "type": "Partial double"},
            {"atom1": "C4", "atom2": "N2", "type": "Single"},
            {"atom1": "N2", "atom2": "O3", "type": "Double"},
            {"atom1": "N2", "atom2": "O4", "type": "Partial double"},
            {"atom1": "C6", "atom2": "N3", "type": "Single"},
            {"atom1": "N3", "atom2": "O5", "type": "Double"},
            {"atom1": "N3", "atom2": "O6", "type": "Partial double"},
        ],
    },
    "ethanol": {
        "name": "Ethanol",
        "formula": "C2H6O",
        "description": "Ethanol molecule (C2H5OH)",
        "atoms": [
            {"id": "C1", "element": "C", "x": 0.000, "y": 0.000, "z": 0.000},
            {"id": "C2", "element": "C", "x": 1.512, "y": 0.000, "z": 0.000},
            {"id": "O1", "element": "O", "x": 2.057, "y": 1.309, "z": 0.000},
            {"id": "H1", "element": "H", "x": -0.380, "y": 1.026, "z": 0.000},
            {"id": "H2", "element": "H", "x": -0.380, "y": -0.513, "z": 0.889},
            {"id": "H3", "element": "H", "x": -0.380, "y": -0.513, "z": -0.889},
            {"id": "H4", "element": "H", "x": 1.892, "y": -0.513, "z": 0.889},
            {"id": "H5", "element": "H", "x": 1.892, "y": -0.513, "z": -0.889},
            {"id": "H6", "element": "H", "x": 3.018, "y": 1.309, "z": 0.000},
        ],
        "bonds": [
            {"atom1": "C1", "atom2": "C2", "type": "Single"},
            {"atom1": "C2", "atom2": "O1", "type": "Single"},
            {"atom1": "C1", "atom2": "H1", "type": "Single"},
            {"atom1": "C1", "atom2": "H2", "type": "Single"},
            {"atom1": "C1", "atom2": "H3", "type": "Single"},
            {"atom1": "C2", "atom2": "H4", "type": "Single"},
            {"atom1": "C2", "atom2": "H5", "type": "Single"},
            {"atom1": "O1", "atom2": "H6", "type": "Single"},
        ],
    },
}


def get_molecule_template(template_name: str) -> dict[str, Any] | None:
    """Retrieve a built-in molecule definition by key."""
    key = template_name.strip().lower()
    return MOLECULE_TEMPLATES.get(key)


def list_molecule_templates() -> list[dict[str, str]]:
    """Return all available built-in molecule templates."""
    return [
        {"id": key, "name": val["name"], "formula": val["formula"], "description": val["description"]}
        for key, val in MOLECULE_TEMPLATES.items()
    ]

