"""Slice — cross-section by plane or along axis."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

SLICE_MODES = ["plane", "along_axis", "orthogonal"]
AXES = ["x", "y", "z"]


class Slice(IO.ComfyNode):
    """Create cross-section slices of a mesh."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaSlice",
            display_name="Slice",
            description="Cross-section by plane, multiple slices along axis, or three orthogonal slices.",
            category="pyvista/filters",
            search_aliases=["slice", "cross section", "section cut"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Combo.Input("mode", options=SLICE_MODES, default="plane"),
                IO.Combo.Input("axis", options=AXES, default="x",
                               tooltip="Axis for plane normal or slice direction."),
                IO.Float.Input("origin_offset", default=0.0, min=-1000.0, max=1000.0, step=0.01,
                               tooltip="Offset from mesh center along axis (plane mode)."),
                IO.Int.Input("n_slices", default=5, min=1, max=100, step=1,
                             tooltip="Number of evenly spaced slices (along_axis mode)."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="slices"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, mode: str, axis: str,
                origin_offset: float, n_slices: int) -> IO.NodeOutput:
        normal_map = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}

        if mode == "plane":
            origin = list(pyvista_geom.center)
            axis_idx = {"x": 0, "y": 1, "z": 2}[axis]
            origin[axis_idx] += origin_offset
            result = pyvista_geom.slice(normal=normal_map[axis], origin=origin)
            desc = f"Plane slice ({axis}, offset={origin_offset})"

        elif mode == "along_axis":
            result = pyvista_geom.slice_along_axis(n=n_slices, axis=axis)
            desc = f"{n_slices} slices along {axis}"

        elif mode == "orthogonal":
            result = pyvista_geom.slice_orthogonal()
            desc = "Orthogonal slices (XY, XZ, YZ)"

        else:
            raise ValueError(f"Unknown mode: {mode}")

        info = f"{desc}: {result.n_points:,} points, {result.n_cells:,} cells"
        return IO.NodeOutput(result, info, ui={"text": [info]})
