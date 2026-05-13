"""
Materials Studio COM client wrapper.
Provides a Pythonic interface to Materials Studio via COM automation.
"""

from __future__ import annotations
import os
import sys
import logging
import tempfile
from pathlib import Path
from typing import Optional, Any
from dataclasses import asdict

from .models.structures import StructureData, LatticeParameters, AtomSite, SimulationResult
from .models.jobs import JobConfig, JobInfo, JobStatus, SimulationType

logger = logging.getLogger(__name__)


class MSClientError(Exception):
    pass


class MSConnectionError(MSClientError):
    pass


class MSModuleNotFoundError(MSClientError):
    pass


class MaterialsStudioClient:
    """
    Wrapper around Materials Studio COM automation API.
    Supports both direct COM access and file-based workflows.
    """

    def __init__(self, visible: bool = False):
        self._app: Any = None
        self._connected = False
        self._visible = visible
        self._documents: dict[str, Any] = {}
        self._jobs: dict[str, JobInfo] = {}

    # ── Connection Management ──────────────────────────────────

    def connect(self) -> bool:
        try:
            import win32com.client
            self._app = win32com.client.Dispatch("MaterialsStudio.Application")
            self._app.Visible = self._visible
            self._connected = True
            logger.info("Connected to Materials Studio")
            return True
        except ImportError:
            logger.warning("pywin32 not installed; MS COM unavailable")
            raise MSConnectionError("pywin32 package required for MS COM integration")
        except Exception as e:
            logger.warning(f"Could not connect to Materials Studio: {e}")
            raise MSConnectionError(
                "Cannot connect to Materials Studio. Ensure MS is installed "
                "and licensed. Error: " + str(e)
            )

    @property
    def is_connected(self) -> bool:
        return self._connected

    def disconnect(self):
        if self._app:
            try:
                self._app.Quit()
            except Exception:
                pass
        self._app = None
        self._connected = False
        self._documents.clear()

    # ── Document Management ────────────────────────────────────

    def open_document(self, path: str) -> Any:
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            raise MSClientError(f"File not found: {abs_path}")
        try:
            doc = self._app.Documents.Open(abs_path)
            self._documents[abs_path] = doc
            return doc
        except Exception as e:
            raise MSClientError(f"Failed to open document: {e}")

    def close_document(self, path: str):
        abs_path = os.path.abspath(path)
        doc = self._documents.pop(abs_path, None)
        if doc:
            try:
                doc.Close()
            except Exception:
                pass

    def save_document(self, path: str, format: str = "xsd") -> str:
        abs_path = os.path.abspath(path)
        doc = self._documents.get(abs_path)
        if doc:
            try:
                doc.SaveAs(abs_path)
                return abs_path
            except Exception as e:
                raise MSClientError(f"Failed to save document: {e}")
        raise MSClientError(f"No open document for: {abs_path}")

    def get_active_document(self) -> Any:
        try:
            return self._app.ActiveDocument
        except Exception as e:
            raise MSClientError(f"No active document: {e}")

    # ── Structure Creation ─────────────────────────────────────

    def create_crystal(
        self,
        name: str,
        space_group: str,
        a: float,
        b: float,
        c: float,
        alpha: float,
        beta: float,
        gamma: float,
    ) -> StructureData:
        try:
            doc = self._app.NewDocument("3DAtomistic")
            doc.Name = name

            lattice = doc.Lattice
            lattice.SetLattice(3, a, b, c, alpha, beta, gamma)
            doc.SpaceGroup = space_group

            doc_path = os.path.join(tempfile.gettempdir(), f"{name}.xsd")
            doc.SaveAs(doc_path)
            self._documents[doc_path] = doc

            return StructureData(
                name=name,
                lattice=LatticeParameters(
                    a=a, b=b, c=c, alpha=alpha, beta=beta, gamma=gamma
                ),
                space_group=space_group,
                file_path=doc_path,
            )
        except Exception as e:
            raise MSClientError(f"Failed to create crystal: {e}")

    def add_atoms(
        self,
        structure: StructureData,
        elements: list[str],
        coords: list[tuple[float, float, float]],
    ) -> StructureData:
        doc_path = structure.file_path
        if not doc_path or doc_path not in self._documents:
            raise MSClientError("Structure document not open")
        doc = self._documents[doc_path]
        try:
            atoms = doc.Atoms
            for el, (x, y, z) in zip(elements, coords):
                atom = atoms.Add()
                atom.Element = el
                atom.X = x
                atom.Y = y
                atom.Z = z
                structure.atoms.append(AtomSite(element=el, x=x, y=y, z=z))
            doc.Save()
            return structure
        except Exception as e:
            raise MSClientError(f"Failed to add atoms: {e}")

    def import_structure(self, path: str) -> StructureData:
        abs_path = os.path.abspath(path)
        doc = self.open_document(abs_path)
        try:
            doc_name = Path(abs_path).stem
            atoms_list = []
            try:
                atoms_enum = doc.Atoms
                for atom in atoms_enum:
                    atoms_list.append(
                        AtomSite(
                            element=atom.Element,
                            x=atom.X,
                            y=atom.Y,
                            z=atom.Z,
                        )
                    )
            except Exception:
                pass

            lattice_data = None
            try:
                lat = doc.Lattice
                lattice_data = LatticeParameters(
                    a=lat.A, b=lat.B, c=lat.C,
                    alpha=lat.Alpha, beta=lat.Beta, gamma=lat.Gamma,
                )
            except Exception:
                pass

            spg = None
            try:
                spg = doc.SpaceGroup
            except Exception:
                pass

            return StructureData(
                name=doc_name,
                lattice=lattice_data,
                atoms=atoms_list,
                space_group=spg,
                file_path=abs_path,
            )
        except Exception as e:
            raise MSClientError(f"Failed to import structure: {e}")

    # ── Simulation ─────────────────────────────────────────────

    def _get_module_dispatch(self, module_name: str) -> Any:
        try:
            if module_name.lower() == "forcite":
                return self._app.Modules.Forcite
            elif module_name.lower() == "castep":
                return self._app.Modules.CASTEP
            elif module_name.lower() == "dmol3":
                return self._app.Modules.DMol3
            else:
                raise MSModuleNotFoundError(f"Unknown module: {module_name}")
        except AttributeError as e:
            raise MSModuleNotFoundError(
                f"Module {module_name} not available in this MS installation"
            ) from e

    def run_forcite(
        self,
        structure_path: str,
        task: str = "GeometryOptimization",
        parameters: Optional[dict] = None,
    ) -> SimulationResult:
        abs_path = os.path.abspath(structure_path)
        doc = self.open_document(abs_path)
        try:
            forcite = self._get_module_dispatch("Forcite")

            calc = forcite.Calculation
            calc.Document = doc

            task_map = {
                "geometry_optimization": "GeometryOptimization",
                "dynamics": "Dynamics",
                "energy": "Energy",
                "anneal": "Anneal",
            }
            calc.Task = task_map.get(task.lower(), task)

            if parameters:
                for key, val in parameters.items():
                    setattr(calc, key, val)

            calc.Run()

            job_id = f"forcite_{Path(abs_path).stem}_{task}"
            result = SimulationResult(
                job_id=job_id,
                status="running",
            )

            job_info = JobInfo(
                job_id=job_id,
                config=JobConfig(
                    simulation_type=SimulationType.FORCITE_GEOMETRY_OPTIMIZATION,
                    name=f"Forcite {task} on {Path(abs_path).name}",
                    parameters=parameters or {},
                    structure_file=abs_path,
                ),
                status=JobStatus.RUNNING,
            )
            self._jobs[job_id] = job_info

            return result
        except Exception as e:
            raise MSClientError(f"Forcite calculation failed: {e}")

    def run_castep(
        self,
        structure_path: str,
        parameters: Optional[dict] = None,
    ) -> SimulationResult:
        abs_path = os.path.abspath(structure_path)
        doc = self.open_document(abs_path)
        try:
            castep = self._get_module_dispatch("CASTEP")
            calc = castep.Calculation
            calc.Document = doc

            if parameters:
                for key, val in parameters.items():
                    setattr(calc, key, val)

            calc.Run()

            job_id = f"castep_{Path(abs_path).stem}"
            result = SimulationResult(job_id=job_id, status="running")

            job_info = JobInfo(
                job_id=job_id,
                config=JobConfig(
                    simulation_type=SimulationType.CASTEP,
                    name=f"CASTEP on {Path(abs_path).name}",
                    parameters=parameters or {},
                    structure_file=abs_path,
                ),
                status=JobStatus.RUNNING,
            )
            self._jobs[job_id] = job_info

            return result
        except Exception as e:
            raise MSClientError(f"CASTEP calculation failed: {e}")

    def run_dmol3(
        self,
        structure_path: str,
        parameters: Optional[dict] = None,
    ) -> SimulationResult:
        abs_path = os.path.abspath(structure_path)
        doc = self.open_document(abs_path)
        try:
            dmol3 = self._get_module_dispatch("DMol3")
            calc = dmol3.Calculation
            calc.Document = doc

            if parameters:
                for key, val in parameters.items():
                    setattr(calc, key, val)

            calc.Run()

            job_id = f"dmol3_{Path(abs_path).stem}"
            result = SimulationResult(job_id=job_id, status="running")

            job_info = JobInfo(
                job_id=job_id,
                config=JobConfig(
                    simulation_type=SimulationType.DMOL3,
                    name=f"DMol3 on {Path(abs_path).name}",
                    parameters=parameters or {},
                    structure_file=abs_path,
                ),
                status=JobStatus.RUNNING,
            )
            self._jobs[job_id] = job_info

            return result
        except Exception as e:
            raise MSClientError(f"DMol3 calculation failed: {e}")

    # ── Job Management ─────────────────────────────────────────

    def get_job_status(self, job_id: str) -> JobInfo:
        job = self._jobs.get(job_id)
        if not job:
            raise MSClientError(f"Job not found: {job_id}")
        return job

    def list_jobs(self) -> list[dict]:
        return [
            {
                "job_id": j.job_id,
                "name": j.config.name,
                "type": j.config.simulation_type.value,
                "status": j.status.value,
                "created": j.created_at.isoformat(),
            }
            for j in self._jobs.values()
        ]

    def wait_for_job(self, job_id: str, poll_interval: float = 2.0) -> JobInfo:
        import time
        job = self._jobs.get(job_id)
        if not job:
            raise MSClientError(f"Job not found: {job_id}")
        while job.status in (JobStatus.PENDING, JobStatus.RUNNING):
            time.sleep(poll_interval)
        return job

    def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job:
            raise MSClientError(f"Job not found: {job_id}")
        job.status = JobStatus.CANCELLED
        return True

    # ── Context Manager ────────────────────────────────────────

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
