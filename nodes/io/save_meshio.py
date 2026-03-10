"""Save Mesh (meshio) — universal mesh writer supporting 30+ formats."""

from __future__ import annotations

import logging
import os

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

log = logging.getLogger("comfyui-pyvista")

MESHIO_WRITE_FORMATS = [
    "auto",
    "abaqus", "ansys-msh", "nastran", "flac3d",
    "gmsh", "medit", "netgen", "su2",
    "exodus", "med", "h5m", "xdmf",
    "obj", "off", "ply", "stl",
    "vtk", "vtu", "vtp",
    "dolfin-xml", "mdpa", "ugrid", "wkt",
]


class SaveMeshio(IO.ComfyNode):
    """Save a PyVista mesh to disk using meshio (30+ formats)."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaSaveMeshio",
            display_name="Save Mesh (meshio)",
            description="Universal mesh writer via meshio — Abaqus, ANSYS, Gmsh, Nastran, VTK, STL, OBJ, PLY, and more.",
            category="pyvista/io",
            search_aliases=["save mesh", "export mesh", "write mesh"],
            is_output_node=True,
            inputs=[
                PyVistaMesh.Input("pyvista_geom", tooltip="PyVista mesh to save."),
                IO.String.Input(
                    "file_path",
                    default="output.vtu",
                    tooltip="Output file path. Extension determines format when 'auto' is selected.",
                ),
                IO.Combo.Input(
                    "file_format",
                    options=MESHIO_WRITE_FORMATS,
                    default="auto",
                    tooltip="Explicit format override. 'auto' detects from file extension.",
                ),
            ],
            outputs=[
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, file_path: str, file_format: str) -> IO.NodeOutput:
        fmt = None if file_format == "auto" else file_format

        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)

        log.info("Saving %s (format=%s)", file_path, fmt or "auto")
        pv.save_meshio(file_path, pyvista_geom, file_format=fmt)

        size_bytes = os.path.getsize(file_path)
        if size_bytes < 1024:
            size_str = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

        info = f"Saved: {file_path} ({size_str})"
        log.info(info)

        return IO.NodeOutput(info, ui={"text": [info]})
