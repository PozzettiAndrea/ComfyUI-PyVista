"""Clip — clip mesh by plane, box, or scalar value."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

CLIP_MODES = ["plane", "box", "scalar"]
PLANE_NORMALS = ["x", "y", "z", "-x", "-y", "-z"]


class Clip(IO.ComfyNode):
    """Clip a mesh by a plane, bounding box, or scalar threshold."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaClip",
            display_name="Clip",
            description="Clip mesh by plane (with normal and origin), bounding box, or scalar value.",
            category="pyvista/filters",
            search_aliases=["clip", "cut", "clip plane", "clip box"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Combo.Input("mode", options=CLIP_MODES, default="plane"),
                IO.Boolean.Input("invert", default=False, tooltip="Invert the clipping region."),
                # Plane params
                IO.Combo.Input("normal", options=PLANE_NORMALS, default="x",
                               tooltip="Plane normal direction (plane mode)."),
                IO.Float.Input("origin_offset", default=0.0, min=-1000.0, max=1000.0, step=0.01,
                               tooltip="Offset along normal from mesh center (plane mode)."),
                # Scalar params
                IO.String.Input("scalar_name", default="",
                                tooltip="Point/cell data array name (scalar mode)."),
                IO.Float.Input("scalar_value", default=0.0, min=-1e6, max=1e6, step=0.01,
                               tooltip="Clip value (scalar mode)."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, mode: str, invert: bool,
                normal: str, origin_offset: float,
                scalar_name: str, scalar_value: float) -> IO.NodeOutput:
        n_before = pyvista_geom.n_cells

        if mode == "plane":
            normal_map = {
                "x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1),
                "-x": (-1, 0, 0), "-y": (0, -1, 0), "-z": (0, 0, -1),
            }
            n_vec = normal_map[normal]
            center = list(pyvista_geom.center)
            axis = {"x": 0, "y": 1, "z": 2, "-x": 0, "-y": 1, "-z": 2}[normal]
            center[axis] += origin_offset
            result = pyvista_geom.clip(normal=n_vec, origin=center, invert=invert)

        elif mode == "box":
            result = pyvista_geom.clip_box(pyvista_geom.bounds, invert=invert)

        elif mode == "scalar":
            name = scalar_name or None
            result = pyvista_geom.clip_scalar(scalars=name, value=scalar_value, invert=invert)

        else:
            raise ValueError(f"Unknown mode: {mode}")

        info = f"Clip ({mode}): {n_before:,} -> {result.n_cells:,} cells"
        return IO.NodeOutput(result, info, ui={"text": [info]})
