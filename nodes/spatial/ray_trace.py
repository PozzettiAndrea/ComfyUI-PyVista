"""Ray Trace — cast rays and find intersections."""

from __future__ import annotations

import numpy as np
import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh


class RayTrace(IO.ComfyNode):
    """Cast a ray and find intersection points with a mesh."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaRayTrace",
            display_name="Ray Trace",
            description="Cast a ray from origin in a direction and find all intersection points with the mesh.",
            category="pyvista/spatial",
            search_aliases=["ray trace", "ray cast", "intersection", "visibility"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Float.Input("origin_x", default=0.0, min=-1e6, max=1e6, step=0.1),
                IO.Float.Input("origin_y", default=0.0, min=-1e6, max=1e6, step=0.1),
                IO.Float.Input("origin_z", default=0.0, min=-1e6, max=1e6, step=0.1),
                IO.Float.Input("direction_x", default=1.0, min=-1e6, max=1e6, step=0.1),
                IO.Float.Input("direction_y", default=0.0, min=-1e6, max=1e6, step=0.1),
                IO.Float.Input("direction_z", default=0.0, min=-1e6, max=1e6, step=0.1),
                IO.Boolean.Input("first_point_only", default=False,
                                 tooltip="If True, only return the first intersection point."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="hit_points"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet,
                origin_x: float, origin_y: float, origin_z: float,
                direction_x: float, direction_y: float, direction_z: float,
                first_point_only: bool) -> IO.NodeOutput:
        if not isinstance(pyvista_geom, pv.PolyData):
            pyvista_geom = pyvista_geom.extract_surface()

        origin = (origin_x, origin_y, origin_z)
        end = (origin_x + direction_x * 1e6,
               origin_y + direction_y * 1e6,
               origin_z + direction_z * 1e6)

        hit_points, hit_cells = pyvista_geom.ray_trace(origin, end, first_point=first_point_only)

        if len(hit_points) > 0:
            result = pv.PolyData(np.array(hit_points))
            result.point_data["cell_id"] = np.array(hit_cells)
        else:
            result = pv.PolyData()

        info = (
            f"Ray: origin={origin}, dir=({direction_x}, {direction_y}, {direction_z})\n"
            f"Hits: {len(hit_points)}"
        )
        return IO.NodeOutput(result, info, ui={"text": [info]})
