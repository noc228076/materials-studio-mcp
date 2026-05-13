from __future__ import annotations
import os
import logging
from typing import Any

from materials_studio_mcp.ms_client import MaterialsStudioClient, MSClientError, MSConnectionError

logger = logging.getLogger(__name__)


def register_analysis_tools(mcp: Any, ms: MaterialsStudioClient):

    @mcp.tool()
    def analyze_forcite_energy(
        structure_file: str,
        force_field: str = "COMPASSIII",
    ) -> str:
        """
        Analyze energy components of a structure using Forcite.

        Args:
            structure_file: Path to the structure file (.xsd)
            force_field: Force field to use
        """
        abs_path = os.path.abspath(structure_file)
        if not os.path.exists(abs_path):
            return f"Error: Structure file not found: {abs_path}"

        try:
            doc = ms.open_document(abs_path)
            forcite = ms._app.Modules.Forcite
            analysis = forcite.Analysis

            energy = analysis.Energy(doc, ForceField=force_field)

            result_parts = [
                f"Forcite Energy Analysis for {os.path.basename(abs_path)}:",
                f"  Force field: {force_field}",
                f"  Potential Energy: {getattr(energy, 'PotentialEnergy', 'N/A')} kcal/mol",
                f"  Kinetic Energy: {getattr(energy, 'KineticEnergy', 'N/A')} kcal/mol",
                f"  Total Energy: {getattr(energy, 'TotalEnergy', 'N/A')} kcal/mol",
            ]

            for attr in ["ValenceEnergy", "NonBondEnergy", "CrossTermEnergy"]:
                val = getattr(energy, attr, None)
                if val is not None:
                    result_parts.append(f"  {attr}: {val} kcal/mol")

            return "\n".join(result_parts)
        except (MSClientError, MSConnectionError) as e:
            return f"Error: {e}"

    @mcp.tool()
    def analyze_structure_properties(
        structure_file: str,
        properties: list[str] | None = None,
    ) -> str:
        """
        Calculate structural properties.

        Args:
            structure_file: Path to the structure file (.xsd)
            properties: Properties to calculate
                       (Density, Volume, SurfaceArea, Porosity, VoidVolume)
        """
        abs_path = os.path.abspath(structure_file)
        if not os.path.exists(abs_path):
            return f"Error: Structure file not found: {abs_path}"

        if properties is None:
            properties = ["Density", "Volume"]

        try:
            doc = ms.open_document(abs_path)
            result_parts = [f"Properties for {os.path.basename(abs_path)}:"]

            if "Volume" in properties:
                try:
                    lat = doc.Lattice
                    vol = lat.Volume
                    result_parts.append(f"  Volume: {vol:.4f} A^3")
                except Exception:
                    result_parts.append("  Volume: N/A (no periodic cell)")

            atoms_data = []
            try:
                for atom in doc.Atoms:
                    atoms_data.append({
                        "element": atom.Element,
                        "mass": getattr(atom, "AtomicMass", 0),
                    })
            except Exception:
                pass

            if "Density" in properties and atoms_data:
                total_mass = sum(
                    a["mass"] for a in atoms_data if a["mass"]
                )
                try:
                    lat = doc.Lattice
                    vol = lat.Volume
                    if vol > 0:
                        density = total_mass / vol
                        result_parts.append(f"  Density: {density:.4f} g/cm^3")
                except Exception:
                    result_parts.append("  Density: N/A")

            if properties:
                for prop in properties:
                    if prop not in ("Volume", "Density"):
                        result_parts.append(f"  {prop}: calculation requires Forcite module")

            return "\n".join(result_parts)
        except (MSClientError, MSConnectionError) as e:
            return f"Error: {e}"

    @mcp.tool()
    def analyze_trajectory(
        trajectory_file: str,
        analysis_type: str = "MSD",
        temperature: float = 298.0,
    ) -> str:
        """
        Analyze a Forcite MD trajectory.

        Args:
            trajectory_file: Path to the trajectory file (.xtd or .his)
            analysis_type: Analysis type (MSD, RDF, DensityProfile, AngleDistribution)
            temperature: Temperature in Kelvin (for MSD diffusion coefficient)
        """
        abs_path = os.path.abspath(trajectory_file)
        if not os.path.exists(abs_path):
            return f"Error: Trajectory file not found: {abs_path}"

        try:
            doc = ms.open_document(abs_path)
            forcite = ms._app.Modules.Forcite
            analysis = forcite.Analysis

            result_parts = [f"Trajectory Analysis for {os.path.basename(abs_path)}:"]

            if analysis_type.upper() == "MSD":
                msd_result = analysis.MSD(doc, Temperature=temperature)
                result_parts.append("  Mean Square Displacement (MSD) Analysis:")
                result_parts.append(f"    Diffusion coefficient: {getattr(msd_result, 'Diffusion', 'N/A')} cm^2/s")
                result_parts.append(f"    MSD: {getattr(msd_result, 'MSD', 'N/A')} A^2")

            elif analysis_type.upper() == "RDF":
                rdf_result = analysis.RDF(doc)
                result_parts.append("  Radial Distribution Function (RDF) Analysis:")
                result_parts.append(f"    Peak positions: {getattr(rdf_result, 'PeakPositions', 'N/A')}")

            else:
                result_parts.append(f"  Analysis type '{analysis_type}' not yet implemented")

            return "\n".join(result_parts)
        except (MSClientError, MSConnectionError) as e:
            return f"Error: {e}"

    @mcp.tool()
    def get_simulation_results(job_id: str) -> str:
        """
        Retrieve results from a completed simulation.

        Args:
            job_id: Job ID of the completed simulation
        """
        try:
            job = ms.get_job_status(job_id)
            if job.status.value != "completed":
                return f"Job '{job_id}' is {job.status.value}. Results are not yet available."

            result_file = job.result_file
            if result_file and os.path.exists(result_file):
                file_info = os.path.getsize(result_file) / 1024
                return (
                    f"Results for job '{job_id}':\n"
                    f"  Status: completed\n"
                    f"  Result file: {result_file}\n"
                    f"  File size: {file_info:.1f} KB\n"
                    f"  Type: {job.config.simulation_type.value}"
                )
            return (
                f"Job '{job_id}' completed but no result file found.\n"
                f"  Check Materials Studio job gateway for output."
            )
        except MSClientError as e:
            return f"Error: {e}"
