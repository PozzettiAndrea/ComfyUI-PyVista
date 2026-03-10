"""Reconstruct Surface — Poisson surface reconstruction from point cloud."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh


class ReconstructSurface(IO.ComfyNode):
    """Poisson surface reconstruction from an oriented point cloud."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaReconstructSurface",
            display_name="Reconstruct Surface",
            description="Poisson surface reconstruction from point cloud with normals. Auto-computes normals if missing.",
            category="pyvista/geometry",
            search_aliases=["reconstruct", "poisson", "point cloud to surface", "surface reconstruction"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom", tooltip="Point cloud (with or without normals)."),
                IO.Int.Input("nbr_sz", default=20, min=5, max=100, step=1,
                             tooltip="Neighborhood size for normal estimation."),
                IO.Int.Input("depth", default=8, min=1, max=14, step=1,
                             tooltip="Octree depth for reconstruction (higher = more detail, slower)."),
                IO.Boolean.Input("compute_normals", default=True,
                                 tooltip="Auto-compute normals if not present."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, nbr_sz: int, depth: int,
                compute_normals: bool) -> IO.NodeOutput:
        if not isinstance(pyvista_geom, pv.PolyData):
            pyvista_geom = pv.PolyData(pyvista_geom.points)

        # Ensure normals exist
        if compute_normals and "Normals" not in pyvista_geom.point_data:
            pyvista_geom = pyvista_geom.compute_normals(point_normals=True, cell_normals=False,
                                        consistent_normals=True, auto_orient_normals=True)

        result = pyvista_geom.reconstruct_surface(nbr_sz=nbr_sz, sample_spacing=None)

        info = (
            f"Surface reconstruction (depth={depth})\n"
            f"Input points: {pyvista_geom.n_points:,}\n"
            f"Result: {result.n_points:,} points, {result.n_cells:,} cells"
        )
        return IO.NodeOutput(result, info, ui={"text": [info]})
