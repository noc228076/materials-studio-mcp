from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LatticeParameters:
    a: float
    b: float
    c: float
    alpha: float
    beta: float
    gamma: float


@dataclass
class AtomSite:
    element: str
    x: float
    y: float
    z: float
    occupancy: float = 1.0


@dataclass
class StructureData:
    name: str
    lattice: Optional[LatticeParameters] = None
    atoms: list[AtomSite] = field(default_factory=list)
    space_group: Optional[str] = None
    file_path: Optional[str] = None
    properties: dict[str, float] = field(default_factory=dict)

    @property
    def composition(self) -> dict[str, int]:
        comp: dict[str, int] = {}
        for atom in self.atoms:
            comp[atom.element] = comp.get(atom.element, 0) + 1
        return comp

    @property
    def num_atoms(self) -> int:
        return len(self.atoms)


@dataclass
class SimulationResult:
    job_id: str
    status: str
    energy_total: Optional[float] = None
    energy_components: dict[str, float] = field(default_factory=dict)
    structure: Optional[StructureData] = None
    trajectory_file: Optional[str] = None
    messages: list[str] = field(default_factory=list)
