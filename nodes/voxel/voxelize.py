"""Voxelize — convert mesh to voxel representation."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh


class Voxelize(IO.ComfyNode):
    """Convert a surface mesh into a voxel representation."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaVoxelize",
            display_name="Voxelize",
            description="Convert a surface mesh to voxels. Returns an UnstructuredGrid of voxel cells.",
            category="pyvista/voxel",
            search_aliases=["voxelize", "voxel", "rasterize", "discretize"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Float.Input("density", default=0.0, min=0.0, max=1000.0, step=0.01,
                               tooltip="Voxel density. 0 = auto (uses mesh resolution heuristic)."),
                IO.Boolean.Input("check_surface", default=True,
                                 tooltip="Check if points are inside the surface (slower but more accurate)."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="voxels"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, density: float, check_surface: bool) -> IO.NodeOutput:
        if not isinstance(pyvista_geom, pv.PolyData):
            pyvista_geom = pyvista_geom.extract_surface()

        d = density if density > 0 else pyvista_geom.length / 50.0
        result = pv.voxelize(pyvista_geom, density=d, check_surface=check_surface)

        info = (
            f"Voxelize (density={d:.4f})\n"
            f"Input: {pyvista_geom.n_points:,} points, {pyvista_geom.n_cells:,} cells\n"
            f"Voxels: {result.n_cells:,} cells"
        )
        return IO.NodeOutput(result, info, ui={"text": [info]})
