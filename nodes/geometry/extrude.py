"""Extrude -- extrude surface along vector or by rotation."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

AXIS_OPTIONS = ["x", "y", "z"]


class Extrude(IO.ComfyNode):
    """Extrude a surface mesh along a vector or by revolution."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaExtrude",
            display_name="Extrude",
            description="Extrude a surface linearly along a vector or by rotation around an axis.",
            category="pyvista/geometry",
            search_aliases=["extrude", "revolve", "sweep"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.DynamicCombo.Input("mode", options=[
                    IO.DynamicCombo.Option("linear", [
                        IO.Float.Input("direction_x", default=0.0, min=-100.0, max=100.0, step=0.1,
                                       tooltip="Extrusion vector X."),
                        IO.Float.Input("direction_y", default=0.0, min=-100.0, max=100.0, step=0.1,
                                       tooltip="Extrusion vector Y."),
                        IO.Float.Input("direction_z", default=1.0, min=-100.0, max=100.0, step=0.1,
                                       tooltip="Extrusion vector Z."),
                    ]),
                    IO.DynamicCombo.Option("rotate", [
                        IO.Float.Input("angle", default=360.0, min=0.0, max=360.0, step=1.0,
                                       tooltip="Rotation angle in degrees."),
                        IO.Int.Input("resolution", default=32, min=3, max=512, step=1,
                                     tooltip="Number of steps in rotation."),
                        IO.Combo.Input("rotation_axis", options=AXIS_OPTIONS, default="z",
                                       tooltip="Axis of rotation."),
                        IO.Float.Input("translation", default=0.0, min=-100.0, max=100.0, step=0.1,
                                       tooltip="Translation along axis during rotation (for springs/helices)."),
                        IO.Float.Input("dradius", default=0.0, min=-100.0, max=100.0, step=0.1,
                                       tooltip="Change in radius during rotation."),
                        IO.Boolean.Input("capping", default=True,
                                         tooltip="Cap the ends of the swept surface."),
                    ]),
                ], tooltip="Extrusion mode: linear along a vector or rotate around an axis."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, mode: dict) -> IO.NodeOutput:
        if not isinstance(pyvista_geom, pv.PolyData):
            pyvista_geom = pyvista_geom.extract_surface()

        selected = mode["mode"]

        if selected == "linear":
            dx = mode["direction_x"]
            dy = mode["direction_y"]
            dz = mode["direction_z"]
            result = pyvista_geom.extrude((dx, dy, dz))
            desc = f"linear ({dx}, {dy}, {dz})"
        else:
            angle = mode["angle"]
            resolution = mode["resolution"]
            axis_name = mode["rotation_axis"]
            translation = mode["translation"]
            dradius = mode["dradius"]
            capping = mode["capping"]
            axis_map = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}
            rotation_axis = axis_map[axis_name]
            result = pyvista_geom.extrude_rotate(
                resolution=resolution,
                angle=angle,
                rotation_axis=rotation_axis,
                translation=translation,
                dradius=dradius,
                capping=capping,
            )
            desc = f"rotate {angle} deg around {axis_name}, {resolution} steps"

        info = f"Extrude ({desc}): {result.n_points:,} points, {result.n_cells:,} cells"
        return IO.NodeOutput(result, info, ui={"text": [info]})
