from __future__ import annotations
import os
import logging
from typing import Any

from materials_studio_mcp.ms_client import MaterialsStudioClient, MSClientError, MSConnectionError

logger = logging.getLogger(__name__)


def register_simulation_tools(mcp: Any, ms: MaterialsStudioClient):

    @mcp.tool()
    def run_forcite_geometry_optimization(
        structure_file: str,
        quality: str = "Medium",
        force_field: str = "COMPASSIII",
        max_iterations: int = 500,
        convergence_level: str = "Fine",
        electrostatics: str = "Ewald",
        van_der_waals: str = "AtomBased",
    ) -> str:
        """
        Run a Forcite geometry optimization calculation.

        Args:
            structure_file: Path to the structure file (.xsd)
            quality: Calculation quality (Ultra-Fine, Fine, Medium, Coarse)
            force_field: Force field (COMPASSIII, COMPASSII, PCFF, CVFF, Universal)
            max_iterations: Maximum number of optimization iterations
            convergence_level: Convergence level (Ultra-Fine, Fine, Medium, Coarse)
            electrostatics: Electrostatic summation method (Ewald, GroupBased, AtomBased)
            van_der_waals: van der Waals summation method (Ewald, GroupBased, AtomBased)
        """
        abs_path = os.path.abspath(structure_file)
        if not os.path.exists(abs_path):
            return f"Error: Structure file not found: {abs_path}"

        try:
            params = {
                "Quality": quality,
                "ForceField": force_field,
                "MaxIterations": max_iterations,
                "ConvergenceLevel": convergence_level,
                "ElectrostaticSummationMethod": electrostatics,
                "VanDerWaalsSummationMethod": van_der_waals,
            }
            result = ms.run_forcite(
                structure_path=abs_path,
                task="geometry_optimization",
                parameters=params,
            )
            return (
                f"Forcite Geometry Optimization submitted\n"
                f"  Job ID: {result.job_id}\n"
                f"  Structure: {abs_path}\n"
                f"  Force field: {force_field}\n"
                f"  Quality: {quality}\n"
                f"  Status: {result.status}\n\n"
                f"Use check_job_status(job_id='{result.job_id}') to monitor progress."
            )
        except (MSClientError, MSConnectionError) as e:
            return f"Error: {e}"

    @mcp.tool()
    def run_forcite_dynamics(
        structure_file: str,
        ensemble: str = "NPT",
        temperature: float = 298.0,
        pressure: float = 1.0,
        time_step: float = 1.0,
        total_time: float = 100.0,
        frame_output_frequency: int = 500,
        quality: str = "Medium",
        force_field: str = "COMPASSIII",
        thermostat: str = "Nose",
        barostat: str = "Berendsen",
    ) -> str:
        """
        Run a Forcite Molecular Dynamics simulation.

        Args:
            structure_file: Path to the structure file (.xsd)
            ensemble: Ensemble (NVE, NVT, NPH, NPT, NPzT)
            temperature: Temperature in Kelvin
            pressure: Pressure in GPa (for NPT, NPH, NPzT)
            time_step: Time step in femtoseconds
            total_time: Total simulation time in picoseconds
            frame_output_frequency: Frame output frequency (steps)
            quality: Calculation quality (Ultra-Fine, Fine, Medium, Coarse)
            force_field: Force field name
            thermostat: Thermostat (Nose, Andersen, NHL)
            barostat: Barostat (Berendsen, Andersen, Parrinello, NHL)
        """
        abs_path = os.path.abspath(structure_file)
        if not os.path.exists(abs_path):
            return f"Error: Structure file not found: {abs_path}"

        try:
            num_steps = int(total_time * 1000 / time_step)
            params = {
                "Quality": quality,
                "ForceField": force_field,
                "Ensemble": ensemble,
                "Temperature": temperature,
                "TimeStep": time_step,
                "TotalSteps": num_steps,
                "FrameOutputFrequency": frame_output_frequency,
                "Thermostat": thermostat,
            }
            if ensemble.upper() in ("NPT", "NPH", "NPZT"):
                params["Pressure"] = pressure
                params["Barostat"] = barostat

            result = ms.run_forcite(
                structure_path=abs_path,
                task="dynamics",
                parameters=params,
            )
            return (
                f"Forcite Molecular Dynamics submitted\n"
                f"  Job ID: {result.job_id}\n"
                f"  Ensemble: {ensemble} at {temperature}K\n"
                f"  Time: {total_time} ps, Step: {time_step} fs, Steps: {num_steps}\n"
                f"  Force field: {force_field}\n"
                f"  Status: {result.status}\n\n"
                f"Use check_job_status(job_id='{result.job_id}') to monitor progress."
            )
        except (MSClientError, MSConnectionError) as e:
            return f"Error: {e}"

    @mcp.tool()
    def run_forcite_energy(
        structure_file: str,
        force_field: str = "COMPASSIII",
        quality: str = "Medium",
        electrostatics: str = "Ewald",
        van_der_waals: str = "AtomBased",
    ) -> str:
        """
        Calculate single-point energy using Forcite.

        Args:
            structure_file: Path to the structure file (.xsd)
            force_field: Force field (COMPASSIII, COMPASSII, PCFF, CVFF, Universal)
            quality: Calculation quality
            electrostatics: Electrostatic summation method
            van_der_waals: van der Waals summation method
        """
        abs_path = os.path.abspath(structure_file)
        if not os.path.exists(abs_path):
            return f"Error: Structure file not found: {abs_path}"

        try:
            params = {
                "Quality": quality,
                "ForceField": force_field,
                "ElectrostaticSummationMethod": electrostatics,
                "VanDerWaalsSummationMethod": van_der_waals,
                "Energy": True,
            }
            result = ms.run_forcite(
                structure_path=abs_path,
                task="energy",
                parameters=params,
            )
            return (
                f"Forcite Energy calculation submitted\n"
                f"  Job ID: {result.job_id}\n"
                f"  Structure: {abs_path}\n"
                f"  Force field: {force_field}\n"
                f"  Status: {result.status}\n\n"
                f"Use check_job_status(job_id='{result.job_id}') to monitor progress."
            )
        except (MSClientError, MSConnectionError) as e:
            return f"Error: {e}"

    @mcp.tool()
    def run_castep_calculation(
        structure_file: str,
        functional: str = "PBE",
        quality: str = "Medium",
        task: str = "GeometryOptimization",
        cut_off_energy: float = 380.0,
        k_points_quality: str = "Medium",
        properties: list[str] | None = None,
    ) -> str:
        """
        Run a CASTEP DFT calculation.

        Args:
            structure_file: Path to the structure file (.xsd)
            functional: Exchange-correlation functional (PBE, PW91, LDA, PBESOL, RPBE, BLYP)
            quality: Calculation quality (Ultra-Fine, Fine, Medium, Coarse)
            task: Calculation task (GeometryOptimization, Energy, Properties, Dynamics)
            cut_off_energy: Plane-wave cut-off energy in eV
            k_points_quality: K-point quality (Ultra-Fine, Fine, Medium, Coarse)
            properties: List of properties to calculate (e.g. ['BandStructure', 'DensityOfStates'])
        """
        abs_path = os.path.abspath(structure_file)
        if not os.path.exists(abs_path):
            return f"Error: Structure file not found: {abs_path}"

        try:
            params = {
                "Functional": functional,
                "Quality": quality,
                "Task": task,
                "CutOffEnergy": cut_off_energy,
                "KPointQuality": k_points_quality,
            }
            if properties:
                params["Properties"] = ",".join(properties)

            result = ms.run_castep(structure_path=abs_path, parameters=params)
            return (
                f"CASTEP calculation submitted\n"
                f"  Job ID: {result.job_id}\n"
                f"  Functional: {functional}\n"
                f"  Quality: {quality}\n"
                f"  Cut-off: {cut_off_energy} eV\n"
                f"  Status: {result.status}\n\n"
                f"Use check_job_status(job_id='{result.job_id}') to monitor progress."
            )
        except (MSClientError, MSConnectionError) as e:
            return f"Error: {e}"

    @mcp.tool()
    def run_dmol3_calculation(
        structure_file: str,
        functional: str = "PBE",
        quality: str = "Medium",
        task: str = "GeometryOptimization",
        basis_set: str = "DNP",
        properties: list[str] | None = None,
    ) -> str:
        """
        Run a DMol3 DFT calculation.

        Args:
            structure_file: Path to the structure file (.xsd)
            functional: Exchange-correlation functional (PBE, PW91, LDA, BLYP, B3LYP)
            quality: Calculation quality (Ultra-Fine, Fine, Medium, Coarse)
            task: Calculation task (GeometryOptimization, Energy, Properties, ElasticConstants)
            basis_set: Basis set (DND, DNP, TNP, DZ, TZ, TZP, TZ2P)
            properties: List of properties (e.g. ['PopulationAnalysis', 'ElectrostaticMoments'])
        """
        abs_path = os.path.abspath(structure_file)
        if not os.path.exists(abs_path):
            return f"Error: Structure file not found: {abs_path}"

        try:
            params = {
                "Functional": functional,
                "Quality": quality,
                "Task": task,
                "BasisSet": basis_set,
            }
            if properties:
                params["Properties"] = ",".join(properties)

            result = ms.run_dmol3(structure_path=abs_path, parameters=params)
            return (
                f"DMol3 calculation submitted\n"
                f"  Job ID: {result.job_id}\n"
                f"  Functional: {functional}\n"
                f"  Basis set: {basis_set}\n"
                f"  Task: {task}\n"
                f"  Status: {result.status}\n\n"
                f"Use check_job_status(job_id='{result.job_id}') to monitor progress."
            )
        except (MSClientError, MSConnectionError) as e:
            return f"Error: {e}"

    @mcp.tool()
    def check_job_status(job_id: str) -> str:
        """
        Check the status of a submitted job.

        Args:
            job_id: Job ID returned from a simulation submission
        """
        try:
            job = ms.get_job_status(job_id)
            return (
                f"Job: {job_id}\n"
                f"  Name: {job.config.name}\n"
                f"  Type: {job.config.simulation_type.value}\n"
                f"  Status: {job.status.value}\n"
                f"  Created: {job.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"  Error: {job.error_message or 'None'}"
            )
        except MSClientError as e:
            return f"Error: {e}"

    @mcp.tool()
    def list_jobs() -> str:
        """
        List all submitted simulation jobs.
        """
        jobs = ms.list_jobs()
        if not jobs:
            return "No jobs submitted yet."
        lines = ["Submitted jobs:"]
        for j in jobs:
            lines.append(
                f"  {j['job_id']:<40s} {j['type']:<30s} {j['status']:<12s} {j['created']}"
            )
        return "\n".join(lines)

    @mcp.tool()
    def cancel_job(job_id: str) -> str:
        """
        Cancel a running or pending job.

        Args:
            job_id: Job ID to cancel
        """
        try:
            ms.cancel_job(job_id)
            return f"Job '{job_id}' has been cancelled."
        except MSClientError as e:
            return f"Error: {e}"
