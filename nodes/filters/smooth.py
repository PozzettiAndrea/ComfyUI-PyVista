"""Smooth — Laplacian and Taubin mesh smoothing."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

METHODS = ["laplacian", "taubin"]


class Smooth(IO.ComfyNode):
    """Smooth mesh surface via Laplacian or Taubin (non-shrinking) methods."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaSmooth",
            display_name="Smooth",
            description="Laplacian smoothing (fast, may shrink) or Taubin smoothing (non-shrinking, volume-preserving).",
            category="pyvista/filters",
            search_aliases=["smooth", "laplacian", "taubin", "denoise"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
                IO.Combo.Input("method", options=METHODS, default="laplacian"),
                IO.Int.Input("iterations", default=20, min=1, max=1000, step=1,
                             tooltip="Number of smoothing iterations."),
                IO.Float.Input("relaxation_factor", default=0.01, min=0.0, max=1.0, step=0.001,
                               tooltip="Relaxation factor per iteration (laplacian only)."),
                IO.Float.Input("pass_band", default=0.1, min=0.0, max=2.0, step=0.01,
                               tooltip="Pass band value for Taubin smoothing (taubin only)."),
                IO.Boolean.Input("boundary_smoothing", default=False,
                                 tooltip="Smooth boundary vertices."),
                IO.Boolean.Input("edge_smoothing", default=False,
                                 tooltip="Smooth sharp edge vertices."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet, method: str, iterations: int,
                relaxation_factor: float, pass_band: float,
                boundary_smoothing: bool, edge_smoothing: bool) -> IO.NodeOutput:
        if not isinstance(pyvista_geom, pv.PolyData):
            pyvista_geom = pyvista_geom.extract_surface()

        if method == "laplacian":
            result = pyvista_geom.smooth(
                n_iter=iterations,
                relaxation_factor=relaxation_factor,
                boundary_smoothing=boundary_smoothing,
                edge_smoothing=edge_smoothing,
            )
        else:
            result = pyvista_geom.smooth_taubin(
                n_iter=iterations,
                pass_band=pass_band,
                boundary_smoothing=boundary_smoothing,
                edge_smoothing=edge_smoothing,
            )

        info = f"Smooth ({method}, {iterations} iters): {result.n_points:,} points"
        return IO.NodeOutput(result, info, ui={"text": [info]})
