"""Load Mesh (meshio) — universal mesh loader supporting 30+ formats."""

from __future__ import annotations

import logging
import os

import meshio
import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

log = logging.getLogger("comfyui-pyvista")

# ComfyUI folder paths
try:
    import folder_paths
    COMFYUI_INPUT_FOLDER = folder_paths.get_input_directory()
except (ImportError, AttributeError):
    COMFYUI_INPUT_FOLDER = None

# Every format meshio can read, grouped for the dropdown.
MESHIO_FORMATS = [
    "auto",
    # Engineering / FEA
    "abaqus", "ansys-msh", "nastran", "flac3d", "permas",
    # Meshing tools
    "gmsh", "medit", "netgen", "tetgen", "su2",
    # Scientific
    "cgns", "exodus", "med", "h5m", "xdmf",
    # Common 3D
    "obj", "off", "ply", "stl",
    # VTK family
    "vtk", "vtu", "vtp", "vts", "vtr", "vti",
    # Other
    "dolfin-xml", "mdpa", "svg", "ugrid", "wkt",
]

# File extensions that meshio can read
# Extensions that PyVista can read natively via VTK readers (skip meshio)
VTK_NATIVE_EXTENSIONS = {".vtk", ".vtu", ".vtp", ".vts", ".vtr", ".vti"}

MESH_EXTENSIONS = [
    ".obj", ".off", ".ply", ".stl",
    ".vtk", ".vtu", ".vtp", ".vts", ".vtr", ".vti",
    ".inp", ".msh", ".nas", ".bdf",
    ".cgns", ".e", ".exo", ".med", ".h5m", ".xdmf",
    ".xml", ".mdpa", ".ugrid", ".wkt", ".mesh", ".vol", ".su2",
    ".f3grid",
]


def get_mesh_files():
    """Get list of available mesh files in the ComfyUI input folder."""
    mesh_files = []

    if COMFYUI_INPUT_FOLDER is None:
        return mesh_files

    # Scan input/3d subdirectory first
    input_3d = os.path.join(COMFYUI_INPUT_FOLDER, "3d")
    if os.path.exists(input_3d):
        for file in os.listdir(input_3d):
            if any(file.lower().endswith(ext) for ext in MESH_EXTENSIONS):
                mesh_files.append(f"3d/{file}")

    # Then scan input root
    for file in os.listdir(COMFYUI_INPUT_FOLDER):
        file_path = os.path.join(COMFYUI_INPUT_FOLDER, file)
        if os.path.isfile(file_path):
            if any(file.lower().endswith(ext) for ext in MESH_EXTENSIONS):
                mesh_files.append(file)

    return sorted(mesh_files)


class LoadMeshio(IO.ComfyNode):
    """Load a mesh file using meshio (30+ formats) and return a PyVista dataset."""

    @classmethod
    def define_schema(cls):
        mesh_files = get_mesh_files()
        if not mesh_files:
            mesh_files = ["No mesh files found in input/"]

        return IO.Schema(
            node_id="PyVistaLoadMeshio",
            display_name="Load Mesh (meshio)",
            description="Universal mesh loader via meshio — Abaqus, ANSYS, Gmsh, Nastran, Medit, VTK, STL, OBJ, PLY, and 25+ more formats.",
            category="pyvista/io",
            search_aliases=["load mesh", "import mesh", "meshio", "read mesh"],
            inputs=[
                IO.Combo.Input(
                    "file_path",
                    options=mesh_files,
                    tooltip="Mesh file from ComfyUI input/ or input/3d/ folder.",
                ),
                IO.Combo.Input(
                    "file_format",
                    options=MESHIO_FORMATS,
                    default="auto",
                    tooltip="Explicit format override. 'auto' detects from file extension.",
                ),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, file_path: str, file_format: str) -> IO.NodeOutput:
        # Resolve to absolute path from input folder
        if COMFYUI_INPUT_FOLDER is not None and not os.path.isabs(file_path):
            abs_path = os.path.join(COMFYUI_INPUT_FOLDER, file_path)
        else:
            abs_path = file_path.strip()

        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"File not found: {abs_path}")

        fmt = None if file_format == "auto" else file_format
        log.info("Loading %s (format=%s)", abs_path, fmt or "auto")

        ext = os.path.splitext(abs_path)[1].lower()
        if ext in VTK_NATIVE_EXTENSIONS and fmt is None:
            pv_mesh = pv.read(abs_path)
        else:
            mio_mesh = meshio.read(abs_path, file_format=fmt)
            pv_mesh = pv.from_meshio(mio_mesh)

        n_points = pv_mesh.n_points
        n_cells = pv_mesh.n_cells
        n_arrays = len(pv_mesh.point_data) + len(pv_mesh.cell_data)
        bounds = pv_mesh.bounds

        info = (
            f"Loaded: {os.path.basename(abs_path)}\n"
            f"Points: {n_points:,}  Cells: {n_cells:,}  Arrays: {n_arrays}\n"
            f"Bounds: x[{bounds[0]:.3f}, {bounds[1]:.3f}] "
            f"y[{bounds[2]:.3f}, {bounds[3]:.3f}] "
            f"z[{bounds[4]:.3f}, {bounds[5]:.3f}]"
        )
        log.info(info)

        return IO.NodeOutput(pv_mesh, info, ui={"text": [info]})
