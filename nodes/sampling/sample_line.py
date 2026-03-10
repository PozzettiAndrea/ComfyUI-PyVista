"""Sample Over Line — probe mesh data along a line."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh


class SampleOverLine(IO.ComfyNode):
    """Probe mesh scalar data along a line between two points."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaSampleLine",
            display_name="Sample Over Line",
            description="Probe mesh scalar/vector data along a line. Returns a line dataset with interpolated values.",
            category="pyvista/sampling",
            search_aliases=["sample line", "probe", "line plot", "plot over line"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Float.Input("start_x", default=0.0, min=-1e6, max=1e6, step=0.1),
                IO.Float.Input("start_y", default=0.0, min=-1e6, max=1e6, step=0.1),
                IO.Float.Input("start_z", default=0.0, min=-1e6, max=1e6, step=0.1),
                IO.Float.Input("end_x", default=1.0, min=-1e6, max=1e6, step=0.1),
                IO.Float.Input("end_y", default=0.0, min=-1e6, max=1e6, step=0.1),
                IO.Float.Input("end_z", default=0.0, min=-1e6, max=1e6, step=0.1),
                IO.Int.Input("resolution", default=100, min=2, max=10000, step=1,
                             tooltip="Number of sample points along the line."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="line"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet,
                start_x: float, start_y: float, start_z: float,
                end_x: float, end_y: float, end_z: float,
                resolution: int) -> IO.NodeOutput:
        a = (start_x, start_y, start_z)
        b = (end_x, end_y, end_z)

        result = pyvista_geom.sample_over_line(a, b, resolution=resolution)

        arrays = list(result.point_data.keys())
        info = (
            f"Sample over line: {resolution} points\n"
            f"From {a} to {b}\n"
            f"Sampled arrays: {arrays}"
        )
        return IO.NodeOutput(result, info, ui={"text": [info]})
