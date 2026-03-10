"""Boolean — CSG union, intersection, difference."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

OPERATIONS = ["union", "intersection", "difference"]


class Boolean(IO.ComfyNode):
    """Perform boolean/CSG operations between two meshes."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaBoolean",
            display_name="Boolean",
            description="CSG boolean operations: union (A + B), intersection (A & B), difference (A - B).",
            category="pyvista/boolean",
            search_aliases=["boolean", "csg", "union", "intersection", "difference", "subtract"],
            inputs=[
                PyVistaMesh.Input("mesh_a", tooltip="First mesh (A)."),
                PyVistaMesh.Input("mesh_b", tooltip="Second mesh (B)."),
                IO.Combo.Input("operation", options=OPERATIONS, default="union"),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, mesh_a: pv.DataSet, mesh_b: pv.DataSet, operation: str) -> IO.NodeOutput:
        a = mesh_a if isinstance(mesh_a, pv.PolyData) else mesh_a.extract_surface()
        b = mesh_b if isinstance(mesh_b, pv.PolyData) else mesh_b.extract_surface()

        if operation == "union":
            result = a.boolean_union(b)
        elif operation == "intersection":
            result = a.boolean_intersection(b)
        elif operation == "difference":
            result = a.boolean_difference(b)
        else:
            raise ValueError(f"Unknown operation: {operation}")

        info = (
            f"Boolean {operation}\n"
            f"A: {a.n_points:,} pts, {a.n_cells:,} cells\n"
            f"B: {b.n_points:,} pts, {b.n_cells:,} cells\n"
            f"Result: {result.n_points:,} pts, {result.n_cells:,} cells"
        )
        return IO.NodeOutput(result, info, ui={"text": [info]})
