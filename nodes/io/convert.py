"""Convert Mesh — bridge between PYVISTA, ComfyUI MESH, and trimesh."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pyvista as pv
import torch
from comfy_api.latest import io as IO
from comfy_api.latest._util import MESH as ComfyMESH

from ..pv_types import PyVistaMesh

log = logging.getLogger("comfyui-pyvista")

# GeometryPack's TRIMESH type string — accepted via io.Custom so this node
# works even when GeometryPack is not installed.
TRIMESH_TYPE = IO.Custom("TRIMESH")


class ConvertMesh(IO.ComfyNode):
    """Bidirectional converter between PYVISTA, ComfyUI MESH, and TRIMESH."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaConvert",
            display_name="Convert Mesh",
            description="Convert between PyVista, ComfyUI MESH, and GeometryPack TRIMESH types.",
            category="pyvista/io",
            search_aliases=["convert mesh", "trimesh to pyvista", "pyvista to trimesh"],
            inputs=[
                PyVistaMesh.Input("pyvista_geom", optional=True, tooltip="PyVista dataset input."),
                IO.Mesh.Input("comfy_mesh", optional=True, tooltip="ComfyUI MESH input (vertices + faces tensors)."),
                TRIMESH_TYPE.Input("trimesh", optional=True, tooltip="GeometryPack TRIMESH input."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.Mesh.Output(display_name="comfy_mesh"),
                TRIMESH_TYPE.Output(display_name="trimesh"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(
        cls,
        pyvista_geom: pv.DataSet | None = None,
        comfy_mesh: ComfyMESH | None = None,
        trimesh: Any | None = None,
    ) -> IO.NodeOutput:
        pv_out = None
        comfy_out = None
        tri_out = None

        if pyvista_geom is not None:
            pv_out = pyvista_geom
            source = "pyvista"
        elif comfy_mesh is not None:
            # ComfyUI MESH -> PyVista
            verts = comfy_mesh.vertices[0].cpu().numpy() if comfy_mesh.vertices.dim() == 3 else comfy_mesh.vertices.cpu().numpy()
            faces_np = comfy_mesh.faces[0].cpu().numpy() if comfy_mesh.faces.dim() == 3 else comfy_mesh.faces.cpu().numpy()
            # PyVista expects [n_verts_per_face, v0, v1, v2, ...] format
            n_faces = len(faces_np)
            pv_faces = np.column_stack([np.full(n_faces, 3, dtype=np.int64), faces_np]).ravel()
            pv_out = pv.PolyData(verts.astype(np.float32), pv_faces)
            source = "comfy_mesh"
        elif trimesh is not None:
            # trimesh.Trimesh -> PyVista
            verts = np.asarray(trimesh.vertices, dtype=np.float32)
            faces_np = np.asarray(trimesh.faces, dtype=np.int64)
            n_faces = len(faces_np)
            pv_faces = np.column_stack([np.full(n_faces, 3, dtype=np.int64), faces_np]).ravel()
            pv_out = pv.PolyData(verts, pv_faces)
            # Copy vertex attributes as point data
            if hasattr(trimesh, "vertex_attributes"):
                for name, arr in trimesh.vertex_attributes.items():
                    pv_out.point_data[name] = np.asarray(arr)
            if hasattr(trimesh, "face_attributes"):
                for name, arr in trimesh.face_attributes.items():
                    pv_out.cell_data[name] = np.asarray(arr)
            source = "trimesh"
        else:
            raise ValueError("At least one mesh input is required.")

        # Build all outputs from the PyVista mesh
        surf = pv_out.extract_surface() if not isinstance(pv_out, pv.PolyData) else pv_out

        # -> ComfyUI MESH
        verts_t = torch.tensor(np.asarray(surf.points), dtype=torch.float32).unsqueeze(0)
        faces_arr = surf.faces.reshape(-1, 4)[:, 1:] if surf.n_cells > 0 else np.zeros((0, 3), dtype=np.int64)
        faces_t = torch.tensor(faces_arr, dtype=torch.int64).unsqueeze(0)
        comfy_out = ComfyMESH(verts_t, faces_t)

        # -> trimesh (best-effort, works if trimesh is installed)
        try:
            import trimesh as trimesh_module
            tri_out = trimesh_module.Trimesh(
                vertices=np.asarray(surf.points),
                faces=faces_arr,
                process=False,
            )
            # Copy point/cell data back as vertex/face attributes
            for name in surf.point_data:
                tri_out.vertex_attributes[name] = np.asarray(surf.point_data[name])
            for name in surf.cell_data:
                tri_out.face_attributes[name] = np.asarray(surf.cell_data[name])
        except ImportError:
            log.warning("trimesh not installed — TRIMESH output will be None")
            tri_out = None

        info = (
            f"Source: {source}\n"
            f"Points: {pv_out.n_points:,}  Cells: {pv_out.n_cells:,}\n"
            f"Point arrays: {list(pv_out.point_data.keys())}\n"
            f"Cell arrays: {list(pv_out.cell_data.keys())}"
        )
        log.info(info)

        return IO.NodeOutput(pv_out, comfy_out, tri_out, info, ui={"text": [info]})
