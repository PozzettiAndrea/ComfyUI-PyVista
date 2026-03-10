"""Compute Normals — generate point and/or cell normals."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh


class ComputeNormals(IO.ComfyNode):
    """Compute point and/or cell normals for a surface mesh."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaComputeNormals",
            display_name="Compute Normals",
            description="Compute point and/or cell normals. Useful for shading, analysis, and downstream operations that require normals.",
            category="pyvista/filters",
            search_aliases=["normals", "compute normals", "point normals", "cell normals"],
            is_output_node=True,
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Boolean.Input("cell_normals", default=True,
                                 tooltip="Compute normals for each cell (face)."),
                IO.Boolean.Input("point_normals", default=True,
                                 tooltip="Compute normals for each point (vertex)."),
                IO.Boolean.Input("flip_normals", default=False,
                                 tooltip="Flip the direction of all normals."),
                IO.Boolean.Input("consistent_normals", default=True,
                                 tooltip="Enforce consistent normal orientation across the mesh."),
                IO.Boolean.Input("split_vertices", default=False,
                                 tooltip="Split vertices at sharp edges (creates hard edges for rendering)."),
                IO.Float.Input("feature_angle", default=30.0, min=0.0, max=180.0, step=1.0,
                               tooltip="Angle (degrees) for splitting vertices at sharp edges. Only used when split_vertices is enabled."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, cell_normals: bool, point_normals: bool,
                flip_normals: bool, consistent_normals: bool, split_vertices: bool,
                feature_angle: float) -> IO.NodeOutput:
        if not isinstance(pyvista_geom, pv.PolyData):
            pyvista_geom = pyvista_geom.extract_surface()

        result = pyvista_geom.compute_normals(
            cell_normals=cell_normals,
            point_normals=point_normals,
            flip_normals=flip_normals,
            consistent_normals=consistent_normals,
            split_vertices=split_vertices,
            feature_angle=feature_angle,
        )

        # Split 3-component Normals into scalar components
        if "Normals" in result.point_data:
            n = result.point_data["Normals"]
            result.point_data["normals_x"] = n[:, 0]
            result.point_data["normals_y"] = n[:, 1]
            result.point_data["normals_z"] = n[:, 2]
        if "Normals" in result.cell_data:
            n = result.cell_data["Normals"]
            result.cell_data["normals_x"] = n[:, 0]
            result.cell_data["normals_y"] = n[:, 1]
            result.cell_data["normals_z"] = n[:, 2]

        parts = []
        if point_normals and "Normals" in result.point_data:
            parts.append(f"Point normals: {result.n_points:,}")
        if cell_normals and "Normals" in result.cell_data:
            parts.append(f"Cell normals: {result.n_cells:,}")
        if flip_normals:
            parts.append("Flipped")
        if split_vertices:
            parts.append(f"Split at {feature_angle:.0f}°")

        info = "Normals computed. " + ", ".join(parts) if parts else "No normals computed."

        # List all field names
        pd_names = list(result.point_data.keys())
        cd_names = list(result.cell_data.keys())
        if pd_names:
            info += f"\nPoint fields: {', '.join(pd_names)}"
        if cd_names:
            info += f"\nCell fields: {', '.join(cd_names)}"
        return IO.NodeOutput(result, info, ui={"text": [info]})
