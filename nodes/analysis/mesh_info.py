"""Mesh Info — comprehensive mesh statistics."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh


class MeshInfo(IO.ComfyNode):
    """Report comprehensive mesh statistics: points, cells, bounds, volume, area, data arrays, topology."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaMeshInfo",
            display_name="Mesh Info",
            description="Comprehensive mesh statistics: points, cells, bounds, volume, area, arrays, manifold check, cell type breakdown.",
            category="pyvista/analysis",
            search_aliases=["mesh info", "mesh stats", "inspect mesh", "mesh properties"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom"),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
                IO.Int.Output(display_name="n_points"),
                IO.Int.Output(display_name="n_cells"),
            ],
        )

    @classmethod
    def execute(cls, pyvista_geom: pv.DataSet) -> IO.NodeOutput:
        n_points = pyvista_geom.n_points
        n_cells = pyvista_geom.n_cells
        bounds = pyvista_geom.bounds

        lines = [
            f"Points: {n_points:,}",
            f"Cells:  {n_cells:,}",
            f"Bounds: x[{bounds[0]:.4f}, {bounds[1]:.4f}]",
            f"        y[{bounds[2]:.4f}, {bounds[3]:.4f}]",
            f"        z[{bounds[4]:.4f}, {bounds[5]:.4f}]",
            f"Center: ({pyvista_geom.center[0]:.4f}, {pyvista_geom.center[1]:.4f}, {pyvista_geom.center[2]:.4f})",
        ]

        # Volume/area (PolyData only)
        if isinstance(pyvista_geom, pv.PolyData):
            lines.append(f"All triangles: {pyvista_geom.is_all_triangles}")
            lines.append(f"N open edges: {pyvista_geom.n_open_edges}")
            try:
                lines.append(f"Is manifold: {pyvista_geom.is_manifold}")
            except Exception:
                pass
            try:
                if pyvista_geom.is_all_triangles and pyvista_geom.n_open_edges == 0:
                    lines.append(f"Volume: {pyvista_geom.volume:.6f}")
                lines.append(f"Area: {pyvista_geom.area:.6f}")
            except Exception:
                pass

        # Cell types
        if hasattr(pyvista_geom, "celltypes") and pyvista_geom.celltypes is not None:
            import numpy as np
            unique, counts = np.unique(pyvista_geom.celltypes, return_counts=True)
            type_strs = [f"  type {int(t)}: {int(c):,}" for t, c in zip(unique, counts)]
            lines.append(f"Cell types ({len(unique)}):")
            lines.extend(type_strs)

        # Data arrays
        if len(pyvista_geom.point_data) > 0:
            lines.append(f"Point data ({len(pyvista_geom.point_data)}): {list(pyvista_geom.point_data.keys())}")
        if len(pyvista_geom.cell_data) > 0:
            lines.append(f"Cell data ({len(pyvista_geom.cell_data)}): {list(pyvista_geom.cell_data.keys())}")
        if len(pyvista_geom.field_data) > 0:
            lines.append(f"Field data ({len(pyvista_geom.field_data)}): {list(pyvista_geom.field_data.keys())}")

        info = "\n".join(lines)
        return IO.NodeOutput(pyvista_geom, info, n_points, n_cells, ui={"text": [info]})
