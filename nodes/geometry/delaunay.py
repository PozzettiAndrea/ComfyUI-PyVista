"""Delaunay — 2D triangulation and 3D tetrahedralization."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

MODES = ["2d", "3d"]


class Delaunay(IO.ComfyNode):
    """Delaunay triangulation (2D) or tetrahedralization (3D) from point clouds."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaDelaunay",
            display_name="Delaunay",
            description="2D: triangulate planar points. 3D: tetrahedralize volume from point cloud.",
            category="pyvista/geometry",
            search_aliases=["delaunay", "triangulate", "tetrahedralize", "point cloud to mesh"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom", tooltip="Point cloud or surface mesh."),
                IO.Combo.Input("mode", options=MODES, default="2d"),
                IO.Float.Input("alpha", default=0.0, min=0.0, max=1000.0, step=0.01,
                               tooltip="Alpha value for filtering. 0 = convex hull."),
                IO.Float.Input("tolerance", default=0.001, min=0.0, max=1.0, step=0.0001,
                               tooltip="Merge tolerance for nearby points."),
                IO.Float.Input("offset", default=1.0, min=0.0, max=100.0, step=0.1,
                               tooltip="Multiplier for the bounding box (2D only)."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, mode: str, alpha: float,
                tolerance: float, offset: float) -> IO.NodeOutput:
        if not isinstance(pyvista_geom, pv.PolyData):
            pyvista_geom = pv.PolyData(pyvista_geom.points)

        if mode == "2d":
            result = pyvista_geom.delaunay_2d(alpha=alpha, tol=tolerance, offset=offset)
            desc = f"2D (alpha={alpha})"
        else:
            result = pyvista_geom.delaunay_3d(alpha=alpha, tol=tolerance)
            desc = f"3D (alpha={alpha})"

        info = f"Delaunay {desc}: {result.n_points:,} points, {result.n_cells:,} cells"
        return IO.NodeOutput(result, info, ui={"text": [info]})
