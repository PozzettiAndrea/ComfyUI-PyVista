"""Compute Curvature — surface curvature as scalar field."""

from __future__ import annotations

import numpy as np
import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

CURVATURE_TYPES = ["mean", "gaussian", "maximum", "minimum"]


class ComputeCurvature(IO.ComfyNode):
    """Compute surface curvature and add it as a point data scalar field."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaCurvature",
            display_name="Compute Curvature",
            description="Compute mean, gaussian, maximum, or minimum curvature. Adds result as point data array.",
            category="pyvista/analysis",
            search_aliases=["curvature", "gaussian curvature", "mean curvature"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Combo.Input("curvature_type", options=CURVATURE_TYPES, default="mean",
                               tooltip="Type of curvature to compute."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, curvature_type: str) -> IO.NodeOutput:
        if not isinstance(pyvista_geom, pv.PolyData):
            pyvista_geom = pyvista_geom.extract_surface()

        result = pyvista_geom.curvature(curv_type=curvature_type)
        arr_name = f"{curvature_type.title()}Curvature" if curvature_type != "gaussian" else "GaussCurvature"

        # The curvature method names the array slightly differently; find it
        for name in result.point_data:
            if "curv" in name.lower():
                arr_name = name
                break

        values = result.point_data[arr_name]
        info = (
            f"{curvature_type.title()} Curvature\n"
            f"Min: {np.min(values):.6f}  Max: {np.max(values):.6f}\n"
            f"Mean: {np.mean(values):.6f}  Std: {np.std(values):.6f}"
        )

        return IO.NodeOutput(result, info, ui={"text": [info]})
