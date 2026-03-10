"""Create Primitive — parametric geometric primitives via PyVista."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

SHAPES = [
    "Sphere", "Box", "Cylinder", "Cone", "Disc", "Plane",
    "Arrow", "Capsule", "Icosphere",
    "Tetrahedron", "Octahedron", "Dodecahedron", "Icosahedron",
]


class CreatePrimitive(IO.ComfyNode):
    """Generate parametric geometric primitives."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaCreatePrimitive",
            display_name="Create Primitive",
            description="Generate geometric primitives: Sphere, Box, Cylinder, Cone, Disc, Plane, Arrow, Capsule, Icosphere, and Platonic solids.",
            category="pyvista/primitives",
            search_aliases=["sphere", "box", "cylinder", "cone", "primitive", "platonic"],
            inputs=[
                IO.Combo.Input("shape", options=SHAPES, default="Sphere"),
                IO.Float.Input("radius", default=1.0, min=0.001, max=100.0, step=0.1,
                               tooltip="Radius (Sphere, Cylinder, Cone, Disc, Capsule, Icosphere)."),
                IO.Float.Input("height", default=1.0, min=0.001, max=100.0, step=0.1,
                               tooltip="Height (Cylinder, Cone, Capsule, Arrow)."),
                IO.Int.Input("resolution", default=32, min=3, max=512, step=1,
                             tooltip="Angular/face resolution."),
                IO.Float.Input("center_x", default=0.0, min=-1000.0, max=1000.0, step=0.1),
                IO.Float.Input("center_y", default=0.0, min=-1000.0, max=1000.0, step=0.1),
                IO.Float.Input("center_z", default=0.0, min=-1000.0, max=1000.0, step=0.1),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, shape: str, radius: float, height: float, resolution: int,
                center_x: float, center_y: float, center_z: float) -> IO.NodeOutput:
        center = (center_x, center_y, center_z)

        if shape == "Sphere":
            mesh = pv.Sphere(radius=radius, center=center, theta_resolution=resolution, phi_resolution=resolution)
        elif shape == "Box":
            half = radius
            mesh = pv.Box(bounds=(-half + center_x, half + center_x,
                                  -half + center_y, half + center_y,
                                  -half + center_z, half + center_z))
        elif shape == "Cylinder":
            mesh = pv.Cylinder(radius=radius, height=height, center=center, resolution=resolution)
        elif shape == "Cone":
            mesh = pv.Cone(radius=radius, height=height, center=center, resolution=resolution)
        elif shape == "Disc":
            mesh = pv.Disc(center=center, outer=radius, inner=0.0, c_res=resolution)
        elif shape == "Plane":
            mesh = pv.Plane(center=center, i_size=radius * 2, j_size=radius * 2,
                            i_resolution=resolution, j_resolution=resolution)
        elif shape == "Arrow":
            mesh = pv.Arrow(start=(center_x, center_y, center_z - height / 2),
                            direction=(0, 0, 1), scale=height)
        elif shape == "Capsule":
            mesh = pv.Capsule(center=center, radius=radius, cylinder_length=height, theta_resolution=resolution)
        elif shape == "Icosphere":
            mesh = pv.Icosphere(radius=radius, center=center, nsub=min(resolution // 8, 5) or 1)
        elif shape == "Tetrahedron":
            mesh = pv.Tetrahedron(radius=radius, center=center)
        elif shape == "Octahedron":
            mesh = pv.Octahedron(radius=radius, center=center)
        elif shape == "Dodecahedron":
            mesh = pv.Dodecahedron(radius=radius, center=center)
        elif shape == "Icosahedron":
            mesh = pv.Icosahedron(radius=radius, center=center)
        else:
            raise ValueError(f"Unknown shape: {shape}")

        info = f"{shape}: {mesh.n_points:,} points, {mesh.n_cells:,} cells"
        return IO.NodeOutput(mesh, info, ui={"text": [info]})
