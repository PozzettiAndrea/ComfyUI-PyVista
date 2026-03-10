"""Extract Feature Edges — boundary, feature, manifold, non-manifold edges."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh


class ExtractFeatureEdges(IO.ComfyNode):
    """Extract boundary, feature, manifold, and non-manifold edges from a mesh."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaFeatureEdges",
            display_name="Extract Feature Edges",
            description="Detect and extract boundary edges, sharp feature edges, manifold edges, and non-manifold edges.",
            category="pyvista/analysis",
            search_aliases=["feature edges", "boundary edges", "open edges", "non-manifold", "detect edges"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Float.Input("feature_angle", default=30.0, min=0.0, max=180.0, step=1.0,
                               tooltip="Dihedral angle threshold for feature edges (degrees)."),
                IO.Boolean.Input("boundary_edges", default=True, tooltip="Extract boundary/open edges."),
                IO.Boolean.Input("feature_edges", default=True, tooltip="Extract sharp feature edges."),
                IO.Boolean.Input("manifold_edges", default=False, tooltip="Extract manifold edges (shared by exactly 2 faces)."),
                IO.Boolean.Input("non_manifold_edges", default=True, tooltip="Extract non-manifold edges (shared by 3+ faces)."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="edges"),
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, feature_angle: float,
                boundary_edges: bool, feature_edges: bool,
                manifold_edges: bool, non_manifold_edges: bool) -> IO.NodeOutput:
        if not isinstance(pyvista_geom, pv.PolyData):
            pyvista_geom = pyvista_geom.extract_surface()

        edges = pyvista_geom.extract_feature_edges(
            feature_angle=feature_angle,
            boundary_edges=boundary_edges,
            feature_edges=feature_edges,
            manifold_edges=manifold_edges,
            non_manifold_edges=non_manifold_edges,
        )

        n_open = pyvista_geom.n_open_edges
        info = (
            f"Feature angle: {feature_angle}\n"
            f"Edge lines extracted: {edges.n_cells:,}\n"
            f"Edge points: {edges.n_points:,}\n"
            f"Open edges on source mesh: {n_open:,}"
        )

        return IO.NodeOutput(edges, pyvista_geom, info, ui={"text": [info]})
