"""Threshold — extract cells within a scalar value range."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh


class Threshold(IO.ComfyNode):
    """Extract cells whose scalar values fall within a given range."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaThreshold",
            display_name="Threshold",
            description="Extract cells within a scalar value range. Select a point/cell data array and define lower/upper bounds.",
            category="pyvista/filters",
            search_aliases=["threshold", "scalar filter", "extract by value", "isovalue"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.String.Input("scalars", default="",
                                tooltip="Name of point/cell data array. Leave empty for active scalars."),
                IO.Float.Input("lower", default=0.0, min=-1e10, max=1e10, step=0.01,
                               tooltip="Lower bound of threshold range."),
                IO.Float.Input("upper", default=1.0, min=-1e10, max=1e10, step=0.01,
                               tooltip="Upper bound of threshold range."),
                IO.Boolean.Input("invert", default=False, tooltip="Invert selection (extract outside range)."),
                IO.Boolean.Input("all_scalars", default=False,
                                 tooltip="If True, all scalars in a cell must satisfy the threshold."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, scalars: str, lower: float, upper: float,
                invert: bool, all_scalars: bool) -> IO.NodeOutput:
        n_before = pyvista_geom.n_cells
        name = scalars if scalars else None

        result = pyvista_geom.threshold(
            value=[lower, upper],
            scalars=name,
            invert=invert,
            all_scalars=all_scalars,
        )

        info = f"Threshold [{lower}, {upper}]: {n_before:,} -> {result.n_cells:,} cells"
        return IO.NodeOutput(result, info, ui={"text": [info]})
