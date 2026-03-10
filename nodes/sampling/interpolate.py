"""Interpolate / Sample — transfer data between meshes."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

MODES = ["interpolate", "sample"]


class Interpolate(IO.ComfyNode):
    """Transfer data from a source mesh onto a target mesh."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaInterpolate",
            display_name="Interpolate / Sample",
            description="'interpolate': RBF interpolation from source points. 'sample': probe source at target locations.",
            category="pyvista/sampling",
            search_aliases=["interpolate", "sample", "probe", "transfer data", "resample"],
            inputs=[
                PyVistaMesh.Input("source", tooltip="Mesh with data arrays to transfer."),
                PyVistaMesh.Input("target", tooltip="Mesh to receive interpolated data."),
                IO.Combo.Input("mode", options=MODES, default="sample"),
                IO.Float.Input("radius", default=0.0, min=0.0, max=1000.0, step=0.01,
                               tooltip="Search radius for interpolation. 0 = auto (interpolate mode)."),
                IO.Float.Input("sharpness", default=2.0, min=0.01, max=100.0, step=0.1,
                               tooltip="RBF kernel sharpness (interpolate mode)."),
                IO.Float.Input("null_value", default=0.0, min=-1e10, max=1e10, step=0.01,
                               tooltip="Value for points outside search radius."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, source: pv.DataSet, target: pv.DataSet, mode: str,
                radius: float, sharpness: float, null_value: float) -> IO.NodeOutput:
        if mode == "interpolate":
            r = radius if radius > 0 else None
            result = target.interpolate(source, radius=r, sharpness=sharpness, null_value=null_value)
            desc = f"interpolate (radius={'auto' if r is None else r}, sharpness={sharpness})"
        else:
            result = target.sample(source)
            desc = "sample (probe)"

        arrays = list(result.point_data.keys())
        info = f"{desc}\nTransferred arrays: {arrays}\nResult: {result.n_points:,} points"
        return IO.NodeOutput(result, info, ui={"text": [info]})
