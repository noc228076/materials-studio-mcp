from __future__ import annotations
import os
import logging
from pathlib import Path
from typing import Any

from materials_studio_mcp.ms_client import MaterialsStudioClient, MSClientError, MSConnectionError
from materials_studio_mcp.utils.file_ops import get_ms_file_info, list_working_directory

logger = logging.getLogger(__name__)


def register_structure_tools(mcp: Any, ms: MaterialsStudioClient):

    @mcp.tool()
    def create_crystal(
        name: str,
        space_group: str,
        a: float,
        b: float,
        c: float,
        alpha: float = 90.0,
        beta: float = 90.0,
        gamma: float = 90.0,
        elements: list[str] | None = None,
        coordinates: list[list[float]] | None = None,
    ) -> str:
        """
        Create a periodic crystal structure in Materials Studio.

        Args:
            name: Structure name
            space_group: Space group symbol (e.g. 'P1', 'Fm-3m', 'P2_1/c')
            a: Lattice parameter a in Angstrom
            b: Lattice parameter b in Angstrom
            c: Lattice parameter c in Angstrom
            alpha: Lattice angle alpha in degrees
            beta: Lattice angle beta in degrees
            gamma: Lattice angle gamma in degrees
            elements: List of element symbols (e.g. ['Si', 'O'])
            coordinates: List of fractional coordinates [[x,y,z], ...]
        """
        try:
            structure = ms.create_crystal(name, space_group, a, b, c, alpha, beta, gamma)

            if elements and coordinates:
                if len(elements) != len(coordinates):
                    return f"Error: elements ({len(elements)}) and coordinates ({len(coordinates)}) count mismatch"
                ms.add_atoms(structure, elements, [(c[0], c[1], c[2]) for c in coordinates])

            result = (
                f"Crystal '{name}' created successfully\n"
                f"  Space group: {space_group}\n"
                f"  Lattice: a={a:.4f}, b={b:.4f}, c={c:.4f}, "
                f"alpha={alpha:.2f}, beta={beta:.2f}, gamma={gamma:.2f}\n"
                f"  Atoms: {structure.num_atoms}\n"
                f"  Saved to: {structure.file_path}"
            )
            return result
        except (MSClientError, MSConnectionError) as e:
            return f"Error: {e}"

    @mcp.tool()
    def create_molecule(
        name: str,
        elements: list[str],
        coordinates: list[list[float]],
        bond_tolerance: float = 0.5,
    ) -> str:
        """
        Create a molecular structure in Materials Studio from atomic coordinates.

        Args:
            name: Molecule name
            elements: Element symbols for each atom (e.g. ['C', 'C', 'O', 'H', 'H', 'H'])
            coordinates: Cartesian coordinates in Angstrom [[x,y,z], ...]
            bond_tolerance: Bond detection tolerance in Angstrom
        """
        try:
            doc = ms._app.NewDocument("3DAtomistic")
            doc.Name = name

            atoms_col = doc.Atoms
            for el, coord in zip(elements, coordinates):
                atom = atoms_col.Add()
                atom.Element = el
                atom.X = coord[0]
                atom.Y = coord[1]
                atom.Z = coord[2]

            doc_path = os.path.join(os.getcwd(), f"{name}.xsd")
            doc.SaveAs(doc_path)

            structure = type("obj", (object,), {
                "name": name, "num_atoms": len(elements),
                "file_path": doc_path, "composition": {}
            })()
            comp = {}
            for el in elements:
                comp[el] = comp.get(el, 0) + 1
            structure.composition = comp

            comp_str = ", ".join(f"{el}={n}" for el, n in sorted(comp.items()))
            return (
                f"Molecule '{name}' created successfully\n"
                f"  Atoms: {structure.num_atoms}\n"
                f"  Composition: {comp_str}\n"
                f"  File: {doc_path}"
            )
        except Exception as e:
            return f"Error creating molecule: {e}"

    @mcp.tool()
    def create_surface(
        name: str,
        crystal_file: str,
        h: int = 1,
        k: int = 0,
        l: int = 0,
        thickness: float = 1.0,
        vacuum: float = 10.0,
    ) -> str:
        """
        Create a surface slab from a bulk crystal structure.

        Args:
            name: Surface structure name
            crystal_file: Path to the bulk crystal .xsd file
            h: Miller index h
            k: Miller index k
            l: Miller index l
            thickness: Slab thickness in Angstrom or layers
            vacuum: Vacuum thickness in Angstrom
        """
        abs_path = os.path.abspath(crystal_file)
        if not os.path.exists(abs_path):
            return f"Error: Crystal file not found: {abs_path}"

        try:
            doc = ms.open_document(abs_path)
            ms._app.RunScript(f"""
                Dim crystal As Document = ActiveDocument
                Dim surface As Document = crystal.CreateSurface({h}, {k}, {l}, {thickness}, {vacuum})
                surface.Name = "{name}"
                surface.SaveAs("{os.path.join(os.getcwd(), name)}.xsd")
            """)

            surface_path = os.path.join(os.getcwd(), f"{name}.xsd")
            return (
                f"Surface '{name}' created successfully\n"
                f"  Miller indices: ({h}{k}{l})\n"
                f"  Slab thickness: {thickness}\n"
                f"  Vacuum: {vacuum} Angstrom\n"
                f"  File: {surface_path}"
            )
        except Exception as e:
            return f"Error creating surface: {e}"

    @mcp.tool()
    def import_structure(file_path: str) -> str:
        """
        Import a structure file into Materials Studio.

        Args:
            file_path: Path to structure file (.xsd, .cif, .mol, .car, .msi)
        """
        try:
            structure = ms.import_structure(file_path)
            comp_str = ", ".join(
                f"{el}={n}" for el, n in sorted(structure.composition.items())
            )
            result = (
                f"Imported: {structure.name}\n"
                f"  Atoms: {structure.num_atoms}\n"
                f"  Composition: {comp_str}\n"
                f"  File: {file_path}"
            )
            if structure.lattice:
                lat = structure.lattice
                result += f"\n  Lattice: a={lat.a:.4f}, b={lat.b:.4f}, c={lat.c:.4f}"
            if structure.space_group:
                result += f"\n  Space group: {structure.space_group}"
            return result
        except (MSClientError, MSConnectionError) as e:
            return f"Error: {e}"

    @mcp.tool()
    def export_structure(source_path: str, output_path: str) -> str:
        """
        Export a structure to a different file format.

        Args:
            source_path: Source structure file path
            output_path: Output file path (extension determines format)
        """
        abs_src = os.path.abspath(source_path)
        abs_dst = os.path.abspath(output_path)

        if not os.path.exists(abs_src):
            return f"Error: Source file not found: {abs_src}"

        try:
            doc = ms.open_document(abs_src)
            doc.SaveAs(abs_dst)
            ms.close_document(abs_src)
            info = get_ms_file_info(abs_dst)
            return (
                f"Exported successfully\n"
                f"  Source: {abs_src}\n"
                f"  Output: {abs_dst}\n"
                f"  Format: {info['format']}"
            )
        except Exception as e:
            return f"Error exporting structure: {e}"

    @mcp.tool()
    def get_structure_info(file_path: str) -> str:
        """
        Get detailed information about a structure file.

        Args:
            file_path: Path to the structure file
        """
        try:
            structure = ms.import_structure(file_path)
            lines = [
                f"Structure: {structure.name}",
                f"  Atoms: {structure.num_atoms}",
            ]
            comp_str = ", ".join(
                f"{el}={n}" for el, n in sorted(structure.composition.items())
            )
            lines.append(f"  Composition: {comp_str}")
            if structure.lattice:
                lat = structure.lattice
                lines.append(
                    f"  Lattice: a={lat.a:.4f}, b={lat.b:.4f}, c={lat.c:.4f}, "
                    f"alpha={lat.alpha:.2f}, beta={lat.beta:.2f}, gamma={lat.gamma:.2f}"
                )
            if structure.space_group:
                lines.append(f"  Space group: {structure.space_group}")
            return "\n".join(lines)
        except (MSClientError, MSConnectionError) as e:
            return f"Error: {e}"

    @mcp.tool()
    def list_structures(directory: str = ".") -> str:
        """
        List Materials Studio structure files in a directory.

        Args:
            directory: Directory to search (default: current directory)
        """
        files = list_working_directory(directory)
        if not files:
            return f"No Materials Studio structure files found in '{directory}'"
        lines = [f"Structure files in '{directory}':"]
        for f in files:
            size_kb = f["size"] / 1024
            lines.append(f"  {f['name']:<30s} {f['format']:<30s} {size_kb:.1f} KB")
        return "\n".join(lines)
