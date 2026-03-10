"""Contour / Isosurface — extract isosurfaces from volumetric data."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh


class Contour(IO.ComfyNode):
    """Extract isosurfaces from volumetric or scalar field data."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaContour",
            display_name="Contour / Isosurface",
            description="Extract isosurfaces at specified scalar values. Works on volumetric grids and surface meshes with scalar fields.",
            category="pyvista/filters",
            search_aliases=["contour", "isosurface", "marching cubes", "level set"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.String.Input("scalars", default="",
                                tooltip="Scalar array name. Leave empty for active scalars."),
                IO.Int.Input("n_contours", default=5, min=1, max=50, step=1,
                             tooltip="Number of evenly spaced isosurface levels."),
                IO.String.Input("isosurface_values", default="",
                                tooltip="Comma-separated explicit isovalues (overrides n_contours if set)."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, scalars: str,
                n_contours: int, isosurface_values: str) -> IO.NodeOutput:
        name = scalars if scalars else None

        if isosurface_values.strip():
            values = [float(v.strip()) for v in isosurface_values.split(",") if v.strip()]
            result = pyvista_geom.contour(isosurfaces=values, scalars=name)
            desc = f"values={values}"
        else:
            result = pyvista_geom.contour(isosurfaces=n_contours, scalars=name)
            desc = f"n={n_contours}"

        info = f"Contour ({desc}): {result.n_points:,} points, {result.n_cells:,} cells"
        return IO.NodeOutput(result, info, ui={"text": [info]})
