"""Cell Quality — per-cell quality metrics."""

from __future__ import annotations

import numpy as np
import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

QUALITY_MEASURES = [
    "area", "aspect_ratio", "condition", "diagonal",
    "jacobian", "max_angle", "max_aspect_frobenius",
    "min_angle", "scaled_jacobian", "shear", "skew",
    "stretch", "taper", "volume", "warpage",
]


class CellQuality(IO.ComfyNode):
    """Compute per-cell quality metric and add it as cell data."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaCellQuality",
            display_name="Cell Quality",
            description="Compute per-cell quality metrics: aspect ratio, skew, jacobian, warpage, angles, and more.",
            category="pyvista/analysis",
            search_aliases=["cell quality", "mesh quality", "aspect ratio", "skew", "jacobian"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Combo.Input("quality_measure", options=QUALITY_MEASURES, default="scaled_jacobian",
                               tooltip="Quality metric to compute."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, quality_measure: str) -> IO.NodeOutput:
        result = pyvista_geom.compute_cell_quality(quality_measure=quality_measure)

        values = result.cell_data["CellQuality"]
        info = (
            f"Quality: {quality_measure}\n"
            f"Min: {np.min(values):.6f}  Max: {np.max(values):.6f}\n"
            f"Mean: {np.mean(values):.6f}  Std: {np.std(values):.6f}\n"
            f"Cells: {result.n_cells:,}"
        )

        return IO.NodeOutput(result, info, ui={"text": [info]})
