"""PYVISTA — a rich 3D geometry type for ComfyUI.

Wraps pyvista.DataSet, which carries:
  - Point data arrays  (scalars, vectors, normals, curvature …)
  - Cell data arrays   (quality metrics, region IDs …)
  - Field data         (metadata key/value pairs)
  - Multiple cell types (tris, quads, tets, hexes, polyhedral …)
  - Full VTK pipeline support

This is intentionally richer than ComfyUI's built-in MESH (vertices + faces
tensors only) and GeometryPack's TRIMESH (surface-only trimesh.Trimesh).
"""

from __future__ import annotations

from typing import Any, Union

import pyvista as pv
from comfy_api.latest._io import ComfyTypeIO, comfytype


@comfytype(io_type="PYVISTA")
class PyVistaMesh(ComfyTypeIO):
    """PyVista dataset — surface meshes, volumetric grids, point clouds, multi-blocks."""

    Type = Union[pv.PolyData, pv.UnstructuredGrid, pv.StructuredGrid,
                 pv.RectilinearGrid, pv.ImageData, pv.MultiBlock]


@comfytype(io_type="PV_PLOTTER")
class PyVistaPlotter(ComfyTypeIO):
    """PyVista Plotter — a configured plotter with subplot grid and added meshes."""

    Type = pv.Plotter
