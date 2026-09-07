"""Pydantic schemas and enums for Materials Studio MCP requests and responses."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


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


class ForciteEnsemble(str, Enum):
    """Molecular dynamics ensembles."""

    NVE = "NVE"
    NVT = "NVT"
    NPT = "NPT"
    NPH = "NPH"


class CastepTask(str, Enum):
    """Supported CASTEP calculation tasks."""

    ENERGY = "Energy"
    GEOM_OPT = "GeometryOptimization"
    BAND_STRUCTURE = "BandStructure"


class CastepQuality(str, Enum):
    """CASTEP calculation quality levels."""

    COARSE = "Coarse"
    MEDIUM = "Medium"
    FINE = "Fine"
    ULTRA_FINE = "Ultra-fine"


class MoleculeAtom(BaseModel):
    """Atom definition used by CreateAtom in MaterialsScript."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str = Field(..., description="Unique atom identifier within the molecule.", min_length=1, max_length=30)
    element: str = Field(..., description="Chemical element symbol.", min_length=1, max_length=3)
    x: float = Field(..., description="Cartesian X coordinate in Angstroms.")
    y: float = Field(..., description="Cartesian Y coordinate in Angstroms.")
    z: float = Field(..., description="Cartesian Z coordinate in Angstroms.")
    formal_charge: int = Field(default=0, description="Optional formal charge.")


class MoleculeBond(BaseModel):
    """Bond definition used by CreateBond in MaterialsScript."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    atom1: str = Field(..., description="Identifier of the first atom.", min_length=1, max_length=30)
    atom2: str = Field(..., description="Identifier of the second atom.", min_length=1, max_length=30)
    type: BondType = Field(default=BondType.SINGLE, description="MaterialsScript bond type.")


class BuildMoleculeInput(BaseModel):
    """Input for building a molecule through MaterialsScript."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(default="Molecule", description="Document and molecule name.", min_length=1, max_length=120)
    output_file: str = Field(..., description="Destination .xsd file path.", min_length=1, max_length=500)
    template: str | None = Field(default=None, description="Optional built-in template name (water, methane, benzene, tnt, ethanol).", max_length=100)
    atoms: list[MoleculeAtom] | None = Field(default=None, description="Atoms to create with CreateAtom.", max_length=500)
    bonds: list[MoleculeBond] = Field(default_factory=list, description="Bonds to create with CreateBond.", max_length=800)
    optimize: bool = Field(default=False, description="If true, run Forcite geometry optimization after building.")
    forcefield: str | None = Field(default="COMPASS", description="Optional Forcite forcefield name.", max_length=100)
    quality: ForciteQuality = Field(default=ForciteQuality.MEDIUM, description="Forcite quality setting.")
    max_iterations: int = Field(default=500, description="Forcite max iterations.", ge=1, le=1_000_000)
    working_dir: str | None = Field(default=None, description="Optional base folder for the job.", max_length=500)
    timeout_seconds: int | None = Field(default=None, description="Execution timeout.", ge=1, le=7 * 24 * 3600)
    dry_run: bool = Field(default=False, description="If true, return generated Perl without executing.")


class StructureSummaryInput(BaseModel):
    """Input for structure inspection."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source_file: str = Field(..., description="Path to structure file.", min_length=1, max_length=500)
    working_dir: str | None = Field(default=None, description="Optional base folder for the job.", max_length=500)
    timeout_seconds: int | None = Field(default=None, description="Execution timeout.", ge=1, le=7 * 24 * 3600)
    dry_run: bool = Field(default=False, description="If true, return generated Perl without executing.")


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
    num_cores: int | None = Field(default=None, description="Parallel cores to allocate (-np).", ge=1, le=256)
    project_mode: bool = Field(default=False, description="Run script inside a project (-project).")
    job_prefix: str = Field(default="custom", description="Prefix for the generated job directory.", min_length=1, max_length=50)
    dry_run: bool = Field(default=False, description="If true, return the script and planned config without launching Materials Studio.")
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON, description="Return format.")


class ValidateScriptInput(BaseModel):
    """Input for MaterialsScript validation."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    script: str = Field(..., description="MaterialsScript Perl source code to check.", min_length=1, max_length=500_000)


class ForciteGeometryOptimizationInput(BaseModel):
    """Input for Forcite geometry optimization."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    input_file: str = Field(..., description="Structure file to import, for example zeolite.xsd or ./models/zeolite.xsd.", min_length=1, max_length=500)
    output_file: str | None = Field(default=None, description="Optional optimized structure export path.", max_length=500)
    forcefield: str = Field(default="COMPASS", description="Forcite forcefield name, for example COMPASS or COMPASSII.", min_length=1, max_length=100)
    quality: ForciteQuality = Field(default=ForciteQuality.MEDIUM, description="Forcite calculation quality.")
    charge_assignment: str = Field(default="Forcefield assigned", description="Forcite charge assignment mode.", min_length=1, max_length=100)
    max_iterations: int = Field(default=500, description="Maximum geometry optimization iterations.", ge=1, le=1_000_000)
    convergence: ForciteConvergence = Field(default=ForciteConvergence.MEDIUM, description="Forcite convergence level.")
    num_cores: int | None = Field(default=None, description="Parallel cores to allocate (-np).", ge=1, le=256)
    working_dir: str | None = Field(default=None, description="Optional base folder for the generated isolated job directory.", max_length=500)
    timeout_seconds: int | None = Field(default=None, description="Execution timeout in seconds.", ge=1, le=7 * 24 * 3600)
    dry_run: bool = Field(default=False, description="If true, return generated Perl without launching Materials Studio.")


ForciteOptimizationInput = ForciteGeometryOptimizationInput


class ImportExportInput(BaseModel):
    """Input for converting structure file formats."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source_file: str = Field(..., description="Source structure file.", min_length=1, max_length=500)
    output_file: str = Field(..., description="Target structure file.", min_length=1, max_length=500)
    working_dir: str | None = Field(default=None, description="Optional base folder for the job.", max_length=500)
    timeout_seconds: int | None = Field(default=None, description="Execution timeout.", ge=1, le=7 * 24 * 3600)
    dry_run: bool = Field(default=False, description="If true, return generated Perl without executing.")


class CrystalAtom(BaseModel):
    """Atom defined in fractional coordinates (u, v, w) within a periodic unit cell."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    element: str = Field(..., description="Chemical element symbol.", min_length=1, max_length=3)
    u: float = Field(..., description="Fractional coordinate along lattice vector a.", ge=-5.0, le=5.0)
    v: float = Field(..., description="Fractional coordinate along lattice vector b.", ge=-5.0, le=5.0)
    w: float = Field(..., description="Fractional coordinate along lattice vector c.", ge=-5.0, le=5.0)
    name: str | None = Field(default=None, description="Optional atom label (e.g. 'Si1', 'O2').", max_length=30)


class BuildCrystalInput(BaseModel):
    """Input for building a 3D periodic crystal structure."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(default="Crystal", description="Structure document name.", min_length=1, max_length=120)
    output_file: str = Field(..., description="Destination .xsd file path.", min_length=1, max_length=500)
    a: float = Field(..., description="Lattice parameter a in Angstroms.", gt=0.1, le=1000.0)
    b: float = Field(..., description="Lattice parameter b in Angstroms.", gt=0.1, le=1000.0)
    c: float = Field(..., description="Lattice parameter c in Angstroms.", gt=0.1, le=1000.0)
    alpha: float = Field(default=90.0, description="Lattice angle alpha in degrees.", gt=0.0, lt=180.0)
    beta: float = Field(default=90.0, description="Lattice angle beta in degrees.", gt=0.0, lt=180.0)
    gamma: float = Field(default=90.0, description="Lattice angle gamma in degrees.", gt=0.0, lt=180.0)
    fractional_atoms: list[CrystalAtom] = Field(default_factory=list, description="List of atoms in fractional coordinates.")
    space_group: str | None = Field(default=None, description="Optional space group name (e.g. 'F m -3 m', 'P 63/m m c', 'P 21/c').", max_length=50)
    working_dir: str | None = Field(default=None, description="Optional job base folder.", max_length=500)
    timeout_seconds: int | None = Field(default=None, description="Execution timeout.", ge=1, le=7 * 24 * 3600)
    dry_run: bool = Field(default=False, description="If true, return generated Perl without executing.")


class BuildSupercellInput(BaseModel):
    """Input for supercell expansion."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source_file: str = Field(..., description="Source crystal structure file (e.g. .xsd, .cif).", min_length=1, max_length=500)
    output_file: str = Field(..., description="Output .xsd path.", min_length=1, max_length=500)
    u: int = Field(default=1, description="Supercell multiple along A axis.", ge=1, le=50)
    v: int = Field(default=1, description="Supercell multiple along B axis.", ge=1, le=50)
    w: int = Field(default=1, description="Supercell multiple along C axis.", ge=1, le=50)
    working_dir: str | None = Field(default=None, description="Optional job base folder.", max_length=500)
    timeout_seconds: int | None = Field(default=None, description="Execution timeout.", ge=1, le=7 * 24 * 3600)
    dry_run: bool = Field(default=False, description="If true, return generated Perl without executing.")


class BuildSurfaceSlabInput(BaseModel):
    """Input for surface cleaving and vacuum slab generation."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source_file: str = Field(..., description="Source 3D crystal structure file (e.g. .xsd, .cif).", min_length=1, max_length=500)
    output_file: str = Field(..., description="Output surface/slab .xsd path.", min_length=1, max_length=500)
    h: int = Field(..., description="Miller index h.")
    k: int = Field(..., description="Miller index k.")
    l: int = Field(..., description="Miller index l.")
    thickness_angstrom: float = Field(default=10.0, description="Slab thickness in Angstroms.", gt=0.1, le=500.0)
    vacuum_angstrom: float = Field(default=15.0, description="Vacuum thickness in Angstroms (0 for 2D surface).", ge=0.0, le=500.0)
    working_dir: str | None = Field(default=None, description="Optional job base folder.", max_length=500)
    timeout_seconds: int | None = Field(default=None, description="Execution timeout.", ge=1, le=7 * 24 * 3600)
    dry_run: bool = Field(default=False, description="If true, return generated Perl without executing.")


class ForciteDynamicsInput(BaseModel):
    """Input for Forcite Molecular Dynamics simulation."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    input_file: str = Field(..., description="Structure file imported into Materials Studio.", min_length=1, max_length=500)
    output_file: str | None = Field(default=None, description="Optional output .xsd trajectory/final structure path.", max_length=500)
    ensemble: ForciteEnsemble = Field(default=ForciteEnsemble.NVT, description="Thermodynamic ensemble (NVT, NPT, NVE, NPH).")
    temperature_k: float = Field(default=298.0, description="Simulation temperature in Kelvin.", gt=0.0, le=10000.0)
    pressure_gpa: float | None = Field(default=None, description="Pressure in GPa for NPT/NPH ensembles.", ge=0.0, le=1000.0)
    time_step_fs: float = Field(default=1.0, description="Time step in femtoseconds.", gt=0.01, le=10.0)
    number_of_steps: int = Field(default=5000, description="Total integration steps.", ge=10, le=100_000_000)
    thermostat: str = Field(default="Nose-Hoover", description="Thermostat method (Nose-Hoover, Berendsen, Andersen).", max_length=50)
    forcefield: str = Field(default="COMPASS", description="Forcefield name (COMPASS, Universal, Dreiding).", min_length=1, max_length=100)
    quality: ForciteQuality = Field(default=ForciteQuality.MEDIUM, description="Forcite calculation quality.")
    num_cores: int | None = Field(default=None, description="Parallel cores to allocate (-np).", ge=1, le=256)
    working_dir: str | None = Field(default=None, description="Optional job base folder.", max_length=500)
    timeout_seconds: int | None = Field(default=None, description="Execution timeout.", ge=1, le=7 * 24 * 3600)
    dry_run: bool = Field(default=False, description="If true, return generated Perl without executing.")


class CastepCalculateInput(BaseModel):
    """Input for executing CASTEP DFT calculation."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    input_file: str = Field(..., description="Structure file imported by CASTEP.", min_length=1, max_length=500)
    output_file: str | None = Field(default=None, description="Optional relaxed structure export path.", max_length=500)
    task: CastepTask = Field(default=CastepTask.ENERGY, description="CASTEP task: Energy, GeometryOptimization, BandStructure.")
    quality: CastepQuality = Field(default=CastepQuality.MEDIUM, description="CASTEP calculation quality.")
    functional: str = Field(default="PBE", description="Exchange-correlation functional (PBE, LDA, PW91, RPBE, WC, PBEsol).", max_length=100)
    cutoff_energy_ev: int | None = Field(default=None, description="Optional plane-wave cutoff energy in eV.", ge=1, le=100_000)
    kpoint_separation: float | None = Field(default=None, description="Optional k-point grid separation (1/Angstrom).", gt=0.0, le=10.0)
    max_iterations: int = Field(default=50, description="Maximum SCF or geometry optimization iterations.", ge=1, le=2000)
    num_cores: int | None = Field(default=None, description="Parallel cores to allocate (-np).", ge=1, le=256)
    working_dir: str | None = Field(default=None, description="Optional job base folder.", max_length=500)
    timeout_seconds: int | None = Field(default=None, description="Execution timeout.", ge=1, le=7 * 24 * 3600)
    dry_run: bool = Field(default=False, description="If true, return generated Perl without executing.")


class ReflexPowderDiffractionInput(BaseModel):
    """Input for Reflex XRD Powder Diffraction simulation."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source_file: str = Field(..., description="Crystal structure file (e.g. .xsd, .cif).", min_length=1, max_length=500)
    output_file: str | None = Field(default=None, description="Optional reflections table export path.", max_length=500)
    two_theta_min: float = Field(default=5.0, description="Minimum 2-theta angle in degrees.", ge=0.0, lt=180.0)
    two_theta_max: float = Field(default=60.0, description="Maximum 2-theta angle in degrees.", gt=0.0, le=180.0)
    step_size: float = Field(default=0.02, description="2-theta step size in degrees.", gt=0.0001, le=5.0)
    radiation: str = Field(default="Cu Ka", description="X-ray source radiation (e.g. 'Cu Ka', 'Mo Ka', 'Fe Ka').", max_length=50)
    working_dir: str | None = Field(default=None, description="Optional job base folder.", max_length=500)
    timeout_seconds: int | None = Field(default=None, description="Execution timeout.", ge=1, le=7 * 24 * 3600)
    dry_run: bool = Field(default=False, description="If true, return generated Perl without executing.")


class CastepEnergyInput(BaseModel):
    """Input for CASTEP Energy script generation."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    input_file: str = Field(..., description="Structure file imported by the CASTEP Energy script.", min_length=1, max_length=500)
    quality: str = Field(default="Medium", description="CASTEP quality setting.", min_length=1, max_length=100)
    task: str = Field(default="Energy", description="CASTEP task name.", min_length=1, max_length=100)
    functional: str = Field(default="PBE", description="Exchange-correlation functional setting.", min_length=1, max_length=100)
    cutoff_energy_ev: int | None = Field(default=None, description="Optional cutoff energy in eV.", ge=1, le=100_000)
    kpoint_separation: float | None = Field(default=None, description="Optional k-point separation.", gt=0, le=10)
