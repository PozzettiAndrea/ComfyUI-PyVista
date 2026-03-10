"""Clean — merge duplicate points, remove degenerate cells."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh


class Clean(IO.ComfyNode):
    """Clean mesh: merge duplicate points, remove degenerate cells, recompute connectivity."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaClean",
            display_name="Clean",
            description="Merge duplicate points within tolerance, remove degenerate cells, and rebuild connectivity.",
            category="pyvista/filters",
            search_aliases=["clean", "merge points", "remove duplicates", "degenerate"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Float.Input("tolerance", default=0.0, min=0.0, max=10.0, step=0.0001,
                               tooltip="Merge tolerance. 0 = auto (uses bounding box diagonal)."),
                IO.Boolean.Input("absolute", default=False,
                                 tooltip="If True, tolerance is absolute distance. If False, relative to bounding box."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, tolerance: float, absolute: bool) -> IO.NodeOutput:
        pts_before = pyvista_geom.n_points
        cells_before = pyvista_geom.n_cells

        tol = tolerance if tolerance > 0 else None
        if not isinstance(pyvista_geom, pv.PolyData):
            pyvista_geom = pyvista_geom.extract_surface()

        result = pyvista_geom.clean(tolerance=tol, absolute=absolute)

        pts_removed = pts_before - result.n_points
        cells_removed = cells_before - result.n_cells
        info = (
            f"Clean: points {pts_before:,} -> {result.n_points:,} ({pts_removed:,} removed)\n"
            f"Cells: {cells_before:,} -> {result.n_cells:,} ({cells_removed:,} removed)"
        )
        return IO.NodeOutput(result, info, ui={"text": [info]})
