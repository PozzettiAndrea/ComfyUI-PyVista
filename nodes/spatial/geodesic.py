"""Geodesic — shortest path and geodesic distance on surface."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

MODES = ["path", "distance"]


class Geodesic(IO.ComfyNode):
    """Compute shortest path between two vertices or geodesic distance field from a source vertex."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaGeodesic",
            display_name="Geodesic",
            description="'path': shortest path between two vertices. 'distance': geodesic distance field from source vertex.",
            category="pyvista/spatial",
            search_aliases=["geodesic", "shortest path", "geodesic distance", "surface distance"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Combo.Input("mode", options=MODES, default="path"),
                IO.Int.Input("source_vertex", default=0, min=0, max=10000000, step=1,
                             tooltip="Source vertex index."),
                IO.Int.Input("target_vertex", default=1, min=0, max=10000000, step=1,
                             tooltip="Target vertex index (path mode only)."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="result"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, mode: str,
                source_vertex: int, target_vertex: int) -> IO.NodeOutput:
        if not isinstance(pyvista_geom, pv.PolyData):
            pyvista_geom = pyvista_geom.extract_surface()

        if mode == "path":
            result = pyvista_geom.geodesic(source_vertex, target_vertex)
            info = (
                f"Geodesic path: vertex {source_vertex} -> {target_vertex}\n"
                f"Path points: {result.n_points:,}\n"
                f"Path cells: {result.n_cells:,}"
            )
        else:
            result = pyvista_geom.geodesic_distance(source_vertex, target_vertex)
            info = (
                f"Geodesic distance from vertex {source_vertex}\n"
                f"Points: {result.n_points:,}"
            )

        return IO.NodeOutput(result, info, ui={"text": [info]})
