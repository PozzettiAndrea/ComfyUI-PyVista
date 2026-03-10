"""Subdivide — mesh subdivision."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

SUBFILTERS = ["linear", "butterfly", "loop"]


class Subdivide(IO.ComfyNode):
    """Subdivide mesh faces to increase resolution."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaSubdivide",
            display_name="Subdivide",
            description="Subdivide mesh: linear (flat split), butterfly (interpolating, preserves shape), loop (approximating smooth).",
            category="pyvista/filters",
            search_aliases=["subdivide", "upsample", "refine", "increase resolution"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Combo.Input("method", options=SUBFILTERS, default="linear"),
                IO.Int.Input("n_subdivisions", default=1, min=1, max=5, step=1,
                             tooltip="Number of subdivision levels. Each level quadruples face count."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, method: str, n_subdivisions: int) -> IO.NodeOutput:
        if not isinstance(pyvista_geom, pv.PolyData):
            pyvista_geom = pyvista_geom.extract_surface()

        n_before = pyvista_geom.n_cells
        result = pyvista_geom.subdivide(n_subdivisions, subfilter=method)

        info = (
            f"Subdivide ({method}, {n_subdivisions}x)\n"
            f"Faces: {n_before:,} -> {result.n_cells:,}\n"
            f"Points: {pyvista_geom.n_points:,} -> {result.n_points:,}"
        )
        return IO.NodeOutput(result, info, ui={"text": [info]})
