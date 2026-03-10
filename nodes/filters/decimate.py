"""Decimate — mesh simplification."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

METHODS = ["decimate", "decimate_pro"]


class Decimate(IO.ComfyNode):
    """Reduce triangle count via decimation."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaDecimate",
            display_name="Decimate",
            description="Reduce triangle count. 'decimate' is fast; 'decimate_pro' preserves topology and features.",
            category="pyvista/filters",
            search_aliases=["decimate", "simplify", "reduce triangles", "LOD"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Combo.Input("method", options=METHODS, default="decimate"),
                IO.Float.Input("target_reduction", default=0.5, min=0.0, max=0.99, step=0.01,
                               tooltip="Fraction of triangles to remove (0.5 = remove 50%)."),
                IO.Boolean.Input("preserve_topology", default=True,
                                 tooltip="Preserve mesh topology (decimate_pro only)."),
                IO.Float.Input("feature_angle", default=45.0, min=0.0, max=180.0, step=1.0,
                               tooltip="Feature edge angle threshold (decimate_pro only)."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, method: str, target_reduction: float,
                preserve_topology: bool, feature_angle: float) -> IO.NodeOutput:
        if not isinstance(pyvista_geom, pv.PolyData):
            pyvista_geom = pyvista_geom.extract_surface()

        n_before = pyvista_geom.n_cells

        if method == "decimate":
            result = pyvista_geom.decimate(target_reduction)
        else:
            result = pyvista_geom.decimate_pro(
                target_reduction,
                preserve_topology=preserve_topology,
                feature_angle=feature_angle,
            )

        pct = (1 - result.n_cells / n_before) * 100 if n_before > 0 else 0
        info = (
            f"Decimate ({method})\n"
            f"Faces: {n_before:,} -> {result.n_cells:,} ({pct:.1f}% removed)\n"
            f"Points: {pyvista_geom.n_points:,} -> {result.n_points:,}"
        )
        return IO.NodeOutput(result, info, ui={"text": [info]})
