"""Warp — deform mesh by scalar or vector field."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

MODES = ["by_scalar", "by_vector"]


class Warp(IO.ComfyNode):
    """Warp/deform mesh geometry based on scalar or vector data arrays."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaWarp",
            display_name="Warp",
            description="Deform mesh vertices using a scalar field (along normals) or a vector field (displacement).",
            category="pyvista/deformation",
            search_aliases=["warp", "deform", "displace", "displacement"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Combo.Input("mode", options=MODES, default="by_scalar"),
                IO.String.Input("array_name", default="",
                                tooltip="Scalar or vector data array name. Leave empty for active scalars/vectors."),
                IO.Float.Input("factor", default=1.0, min=-100.0, max=100.0, step=0.1,
                               tooltip="Scale factor for the deformation."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, mode: str, array_name: str,
                factor: float) -> IO.NodeOutput:
        name = array_name if array_name else None

        if mode == "by_scalar":
            result = pyvista_geom.warp_by_scalar(scalars=name, factor=factor)
            desc = f"by_scalar (factor={factor})"
        else:
            result = pyvista_geom.warp_by_vector(vectors=name, factor=factor)
            desc = f"by_vector (factor={factor})"

        info = f"Warp {desc}: {result.n_points:,} points"
        return IO.NodeOutput(result, info, ui={"text": [info]})
