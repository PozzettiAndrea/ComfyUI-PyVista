"""Connectivity — connected components analysis."""

from __future__ import annotations

import numpy as np
import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

MODES = ["label", "extract_largest"]


class Connectivity(IO.ComfyNode):
    """Label connected components or extract the largest connected region."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaConnectivity",
            display_name="Connectivity",
            description="'label': assign RegionId to each connected component. 'extract_largest': keep only the largest component.",
            category="pyvista/connectivity",
            search_aliases=["connectivity", "connected components", "extract largest", "separate bodies"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Combo.Input("mode", options=MODES, default="label"),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, mode: str) -> IO.NodeOutput:
        if mode == "label":
            result = pyvista_geom.connectivity(extraction_mode="all")
            region_ids = result.cell_data.get("RegionId", result.point_data.get("RegionId", []))
            n_regions = len(np.unique(region_ids)) if len(region_ids) > 0 else 0
            info = f"Connectivity: {n_regions} connected components\nCells: {result.n_cells:,}"
        else:
            result = pyvista_geom.connectivity(extraction_mode="largest")
            info = (
                f"Extract largest component\n"
                f"Before: {pyvista_geom.n_cells:,} cells\n"
                f"After: {result.n_cells:,} cells"
            )

        return IO.NodeOutput(result, info, ui={"text": [info]})
