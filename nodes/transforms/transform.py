"""Transform — translate, rotate, scale, reflect, align."""

from __future__ import annotations

import numpy as np
import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

MODES = ["translate", "rotate", "scale", "reflect", "align"]


class Transform(IO.ComfyNode):
    """Apply spatial transforms: translate, rotate, scale, reflect, or ICP alignment."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaTransform",
            display_name="Transform",
            description="Translate, rotate, scale, reflect a mesh, or align to a target mesh via ICP.",
            category="pyvista/transforms",
            search_aliases=["transform", "translate", "rotate", "scale", "reflect", "align", "ICP"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Combo.Input("mode", options=MODES, default="translate"),
                IO.Float.Input("x", default=0.0, min=-1e6, max=1e6, step=0.1,
                               tooltip="X: translation offset / rotation degrees / scale factor / reflect normal."),
                IO.Float.Input("y", default=0.0, min=-1e6, max=1e6, step=0.1,
                               tooltip="Y component."),
                IO.Float.Input("z", default=0.0, min=-1e6, max=1e6, step=0.1,
                               tooltip="Z component."),
                PyVistaMesh.Input("target", optional=True,
                                  tooltip="Target mesh for ICP alignment (align mode only)."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, mode: str, x: float, y: float, z: float,
                target: pv.DataSet | None = None) -> IO.NodeOutput:
        result = pyvista_geom.copy()

        if mode == "translate":
            result = result.translate((x, y, z), inplace=False)
            desc = f"translate ({x}, {y}, {z})"

        elif mode == "rotate":
            if x != 0:
                result = result.rotate_x(x, inplace=False)
            if y != 0:
                result = result.rotate_y(y, inplace=False)
            if z != 0:
                result = result.rotate_z(z, inplace=False)
            desc = f"rotate ({x}, {y}, {z}) deg"

        elif mode == "scale":
            sx = x if x != 0 else 1.0
            sy = y if y != 0 else 1.0
            sz = z if z != 0 else 1.0
            result = result.scale((sx, sy, sz), inplace=False)
            desc = f"scale ({sx}, {sy}, {sz})"

        elif mode == "reflect":
            normal = (x, y, z)
            if np.allclose(normal, 0):
                normal = (1, 0, 0)
            result = result.reflect(normal, inplace=False)
            desc = f"reflect normal=({x}, {y}, {z})"

        elif mode == "align":
            if target is None:
                raise ValueError("Target mesh is required for align mode.")
            result, matrix = result.align(target)
            desc = "ICP align"

        else:
            raise ValueError(f"Unknown mode: {mode}")

        info = f"Transform ({desc}): {result.n_points:,} points"
        return IO.NodeOutput(result, info, ui={"text": [info]})
