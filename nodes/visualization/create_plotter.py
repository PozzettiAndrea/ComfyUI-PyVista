"""Create Plotter — initialize a PyVista plotter with a subplot grid."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaPlotter


class CreatePlotter(IO.ComfyNode):
    """Create a PyVista Plotter with configurable subplot grid layout."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaCreatePlotter",
            display_name="Create Plotter",
            description="Create a PyVista plotter with subplot grid. Use 'Add to Plotter' to populate subplots, then 'Preview Plotter' to display.",
            category="pyvista/visualization",
            search_aliases=["plotter", "subplot", "grid", "multi view"],
            inputs=[
                IO.DynamicCombo.Input(
                    "grid",
                    options=[
                        IO.DynamicCombo.Option("1x1", []),
                        IO.DynamicCombo.Option("1x2", []),
                        IO.DynamicCombo.Option("2x1", []),
                        IO.DynamicCombo.Option("2x2", []),
                        IO.DynamicCombo.Option("custom", [
                            IO.Int.Input("rows", default=2, min=1, max=10,
                                         tooltip="Number of rows."),
                            IO.Int.Input("cols", default=2, min=1, max=10,
                                         tooltip="Number of columns."),
                        ]),
                    ],
                    tooltip="Subplot grid layout. Use 'custom' for arbitrary rows x cols.",
                ),
                IO.Combo.Input("background", options=["default", "white", "black", "dark_gray", "light_gray"],
                               default="default", tooltip="Plotter background color."),
                IO.Boolean.Input("link_views", default=False,
                                 tooltip="Synchronize camera across all subplots."),
            ],
            outputs=[
                PyVistaPlotter.Output(display_name="plotter"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, grid: dict, background: str, link_views: bool) -> IO.NodeOutput:
        selection = grid["grid"]
        if selection == "custom":
            shape = (grid.get("rows", 2), grid.get("cols", 2))
        else:
            r, c = selection.split("x")
            shape = (int(r), int(c))

        pv.OFF_SCREEN = True
        plotter = pv.Plotter(off_screen=True, shape=shape)

        bg_colors = {
            "default": None,
            "white": "white",
            "black": "black",
            "dark_gray": "#2e2e2e",
            "light_gray": "#cccccc",
        }
        bg = bg_colors.get(background)
        if bg:
            for r_idx in range(shape[0]):
                for c_idx in range(shape[1]):
                    plotter.subplot(r_idx, c_idx)
                    plotter.set_background(bg)

        if link_views:
            plotter.link_views()

        # Reset to first subplot
        plotter.subplot(0, 0)

        info = f"Plotter created: {shape[0]}x{shape[1]} grid"
        if link_views:
            info += ", linked views"
        return IO.NodeOutput(plotter, info, ui={"text": [info]})
