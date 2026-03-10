"""Add to Plotter — add a mesh to a specific subplot of a PyVista plotter."""

from __future__ import annotations

import copy

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh, PyVistaPlotter

STYLES = ["surface", "wireframe", "points"]


class AddToPlotter(IO.ComfyNode):
    """Add a mesh to a plotter subplot. Chain multiple to populate a multi-view layout."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaAddToPlotter",
            display_name="Add to Plotter",
            description="Add a mesh to a plotter subplot with display options. Chainable — connect multiple in sequence.",
            category="pyvista/visualization",
            search_aliases=["add mesh", "subplot", "plotter add"],
            inputs=[
                PyVistaPlotter.Input("plotter"),
                PyVistaMesh.Input("pyvista_geom"),
                IO.Int.Input("row", default=0, min=0, max=9,
                             tooltip="Subplot row index (0-based)."),
                IO.Int.Input("col", default=0, min=0, max=9,
                             tooltip="Subplot column index (0-based)."),
                IO.Combo.Input("style", options=STYLES, default="surface",
                               tooltip="Render style for this mesh."),
                IO.String.Input("color", default="",
                                tooltip="Mesh color (e.g. 'red', '#ff0000'). Empty = use scalars or default."),
                IO.String.Input("scalars", default="",
                                tooltip="Scalar array name for colormapping. Empty = first available or solid color."),
                IO.Float.Input("opacity", default=1.0, min=0.0, max=1.0, step=0.05),
                IO.Boolean.Input("show_edges", default=False),
                IO.Float.Input("line_width", default=1.0, min=0.1, max=20.0, step=0.5,
                               tooltip="Line width for wireframe and edges."),
                IO.Float.Input("point_size", default=5.0, min=0.5, max=50.0, step=0.5,
                               tooltip="Point size for 'points' style."),
            ],
            outputs=[
                PyVistaPlotter.Output(display_name="plotter"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, plotter: pv.Plotter, pyvista_geom: pv.DataSet,
                row: int, col: int, style: str, color: str, scalars: str,
                opacity: float, show_edges: bool,
                line_width: float, point_size: float) -> IO.NodeOutput:
        # Select subplot
        plotter.subplot(row, col)

        # Deep copy to avoid shared state between subplots
        mesh_copy = copy.deepcopy(pyvista_geom)

        # Extract surface for display
        if isinstance(mesh_copy, pv.PolyData):
            surf = mesh_copy
        else:
            surf = mesh_copy.extract_surface()

        # Build add_mesh kwargs
        kwargs = {
            "style": style,
            "opacity": opacity,
            "show_edges": show_edges,
            "line_width": line_width,
            "point_size": point_size,
        }

        # Determine color/scalars
        if scalars:
            kwargs["scalars"] = scalars
        elif not color:
            # Auto-detect: use first available scalar (1-component) field
            auto_scalar = None
            for name in surf.point_data:
                arr = surf.point_data[name]
                if arr.ndim == 1:
                    auto_scalar = name
                    break
            if not auto_scalar:
                for name in surf.cell_data:
                    arr = surf.cell_data[name]
                    if arr.ndim == 1:
                        auto_scalar = name
                        break
            if auto_scalar:
                kwargs["scalars"] = auto_scalar
            else:
                kwargs["color"] = "lightblue"

        if color:
            kwargs["color"] = color

        plotter.add_mesh(surf, **kwargs)

        info = f"Added mesh ({surf.n_points:,} pts, {surf.n_cells:,} cells) to subplot [{row},{col}]"
        return IO.NodeOutput(plotter, info, ui={"text": [info]})
