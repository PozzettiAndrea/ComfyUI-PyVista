"""Preview PyVista — interactive 3D preview via trame or static VTK.js viewer."""

from __future__ import annotations

import logging
import os
import uuid

import numpy as np
import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

log = logging.getLogger("comfyui-pyvista")

try:
    import folder_paths
    COMFYUI_OUTPUT_FOLDER = folder_paths.get_output_directory()
except (ImportError, AttributeError):
    COMFYUI_OUTPUT_FOLDER = None

MODES = ["fields", "wireframe", "surface"]


class PreviewPyVista(IO.ComfyNode):
    """Interactive 3D preview using trame (PyVistaLocalView) with static VTK.js fallback."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaPreview",
            display_name="Preview PyVista",
            description="Interactive 3D preview. Uses trame PyVistaLocalView with Vuetify3 controls, falls back to static VTK.js viewer.",
            category="pyvista/visualization",
            search_aliases=["preview", "view", "visualize", "3d viewer"],
            is_output_node=True,
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Combo.Input("mode", options=MODES, default="fields",
                               tooltip="'fields': scalar colormap, 'wireframe': edges only, 'surface': solid color."),
            ],
            hidden=[IO.Hidden.unique_id],
            outputs=[
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, mode: str) -> IO.NodeOutput:
        # Extract surface for display
        if isinstance(pyvista_geom, pv.PolyData):
            surf = pyvista_geom
        else:
            surf = pyvista_geom.extract_surface()

        # Mesh info (shared between trame and static paths)
        bounds = surf.bounds
        extents = [bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]]
        max_extent = max(extents)
        field_names = list(surf.point_data.keys()) + [f"cell:{k}" for k in surf.cell_data.keys()]

        info_lines = [
            f"Points: {surf.n_points:,}  Cells: {surf.n_cells:,}",
            f"Bounds: x[{bounds[0]:.3f}, {bounds[1]:.3f}] y[{bounds[2]:.3f}, {bounds[3]:.3f}] z[{bounds[4]:.3f}, {bounds[5]:.3f}]",
        ]
        if field_names:
            info_lines.append(f"Fields: {field_names}")
        info = "\n".join(info_lines)

        ui_data = {
            "vertex_count": [surf.n_points],
            "face_count": [surf.n_cells],
            "bounds_min": [[bounds[0], bounds[2], bounds[4]]],
            "bounds_max": [[bounds[1], bounds[3], bounds[5]]],
            "extents": [extents],
            "max_extent": [float(max_extent)],
            "field_names": [field_names],
            "viewer_type": [mode],
        }

        # --- Try trame path first ---
        node_id = cls.hidden.unique_id if cls.hidden else None
        if node_id:
            try:
                from . import trame_manager
                trame_url = trame_manager.create_view(node_id, pyvista_geom)
                ui_data["viewer_mode"] = ["trame"]
                ui_data["trame_url"] = [trame_url]
                ui_data["trame_node_id"] = [node_id]
                log.debug("Trame view created for node %s", node_id)
                return IO.NodeOutput(info, ui=ui_data)
            except Exception as e:
                log.warning("Trame view failed, falling back to static viewer: %s", e)

        # --- Fallback: static VTP/STL export for VTK.js viewer ---
        uid = uuid.uuid4().hex[:8]
        has_point_data = len(surf.point_data) > 0
        has_cell_data = len(surf.cell_data) > 0

        if has_point_data or has_cell_data:
            filename = f"pv_preview_{uid}.vtp"
        else:
            filename = f"pv_preview_{uid}.stl"

        if COMFYUI_OUTPUT_FOLDER:
            filepath = os.path.join(COMFYUI_OUTPUT_FOLDER, filename)
        else:
            import tempfile
            filepath = os.path.join(tempfile.gettempdir(), filename)

        try:
            surf.save(filepath)
            log.debug("Exported preview to: %s", filepath)
        except Exception as e:
            log.error("Export failed: %s", e)
            filename = f"pv_preview_{uid}.stl"
            filepath = filepath.rsplit(".", 1)[0] + ".stl"
            surf.save(filepath)

        ui_data["viewer_mode"] = ["static"]
        ui_data["mesh_file"] = [filename]

        return IO.NodeOutput(info, ui=ui_data)
