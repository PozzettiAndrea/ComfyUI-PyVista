"""Preview Plotter — display a fully configured PyVista plotter via trame."""

from __future__ import annotations

import logging
import os
import uuid

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaPlotter

log = logging.getLogger("comfyui-pyvista")

try:
    import folder_paths
    COMFYUI_OUTPUT_FOLDER = folder_paths.get_output_directory()
except (ImportError, AttributeError):
    COMFYUI_OUTPUT_FOLDER = None


class PreviewPlotter(IO.ComfyNode):
    """Render a PyVista Plotter (with subplot grid and meshes) via trame."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaPreviewPlotter",
            display_name="Preview Plotter",
            description="Display a configured plotter via trame. Connect from 'Add to Plotter' chain.",
            category="pyvista/visualization",
            search_aliases=["preview plotter", "render", "display", "multi view"],
            is_output_node=True,
            inputs=[
                PyVistaPlotter.Input("plotter"),
            ],
            hidden=[IO.Hidden.unique_id],
            outputs=[
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, plotter: pv.Plotter) -> IO.NodeOutput:
        # Gather info from plotter
        n_renderers = len(plotter.renderers)
        try:
            total_actors = sum(len(r.actors) for r in plotter.renderers)
        except AttributeError:
            total_actors = 0
        info = f"Plotter: {n_renderers} subplot(s), {total_actors} actor(s)"

        ui_data = {
            "vertex_count": [0],
            "face_count": [0],
            "viewer_type": ["plotter"],
        }

        node_id = cls.hidden.unique_id if cls.hidden else None
        if node_id:
            try:
                from . import trame_manager
                trame_url = trame_manager.create_view_from_plotter(node_id, plotter)
                ui_data["viewer_mode"] = ["trame"]
                ui_data["trame_url"] = [trame_url]
                ui_data["trame_node_id"] = [node_id]
                log.debug("Trame plotter view created for node %s", node_id)
                return IO.NodeOutput(info, ui=ui_data)
            except Exception as e:
                log.warning("Trame plotter view failed: %s", e)
                # Fallback: extract meshes from plotter and export for static viewer
                try:
                    ui_data = _static_fallback(plotter, ui_data)
                except Exception as e2:
                    log.warning("Static fallback also failed: %s", e2)

        return IO.NodeOutput(info, ui=ui_data)


def _static_fallback(plotter: pv.Plotter, ui_data: dict) -> dict:
    """Extract meshes from plotter renderers and export to VTP for static viewer."""
    import numpy as np

    meshes = []
    for renderer in plotter.renderers:
        try:
            actors_dict = renderer.actors
        except AttributeError:
            continue
        for actor in actors_dict.values():
            if hasattr(actor, 'mapper') and actor.mapper and hasattr(actor.mapper, 'dataset'):
                ds = actor.mapper.dataset
                if ds and ds.n_points > 0:
                    meshes.append(ds)
    if not meshes:
        return ui_data

    combined = meshes[0] if len(meshes) == 1 else pv.merge(meshes)
    surf = combined.extract_surface() if not isinstance(combined, pv.PolyData) else combined

    uid = uuid.uuid4().hex[:8]
    filename = f"pv_plotter_{uid}.vtp"

    if COMFYUI_OUTPUT_FOLDER:
        filepath = os.path.join(COMFYUI_OUTPUT_FOLDER, filename)
    else:
        import tempfile
        filepath = os.path.join(tempfile.gettempdir(), filename)

    surf.save(filepath)
    ui_data["viewer_mode"] = ["static"]
    ui_data["mesh_file"] = [filename]
    log.debug("Static fallback exported: %s", filename)
    return ui_data
