"""Create Parametric Surface — mathematical surfaces via PyVista."""

from __future__ import annotations

import pyvista as pv
from comfy_api.latest import io as IO

from ..pv_types import PyVistaMesh

SURFACES = [
    "Torus", "Klein Bottle", "Mobius Strip", "Superquadric", "Ellipsoid",
    "Boy Surface", "Dini Surface", "Enneper", "Roman Surface", "Super Toroid",
]


class CreateParametricSurface(IO.ComfyNode):
    """Generate parametric mathematical surfaces."""

    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="PyVistaParametricSurface",
            display_name="Create Parametric Surface",
            description="Generate mathematical surfaces: Torus, Klein Bottle, Mobius, Superquadric, Ellipsoid, Boy, Dini, Enneper, Roman, Super Toroid.",
            category="pyvista/primitives",
            search_aliases=["torus", "klein", "mobius", "parametric", "superquadric"],
            inputs=[
                IO.Combo.Input("surface", options=SURFACES, default="Torus"),
                IO.Float.Input("param_a", default=1.0, min=0.01, max=50.0, step=0.1,
                               tooltip="Primary parameter: ring radius (Torus), x-radius (Ellipsoid/Superquadric), scale (others)."),
                IO.Float.Input("param_b", default=0.3, min=0.01, max=50.0, step=0.1,
                               tooltip="Secondary parameter: cross-section radius (Torus), y-radius (Ellipsoid), roundness (Superquadric)."),
                IO.Float.Input("param_c", default=0.3, min=0.01, max=50.0, step=0.1,
                               tooltip="Tertiary parameter: z-radius (Ellipsoid), toroid roundness (Superquadric)."),
            ],
            outputs=[
                PyVistaMesh.Output(display_name="pyvista_geom"),
                IO.String.Output(display_name="info"),
            ],
        )

    @classmethod
    def execute(cls, surface: str, param_a: float, param_b: float, param_c: float) -> IO.NodeOutput:
        if surface == "Torus":
            mesh = pv.ParametricTorus(ringradius=param_a, crosssectionradius=param_b)
        elif surface == "Klein Bottle":
            mesh = pv.ParametricKleinBottle()
        elif surface == "Mobius Strip":
            mesh = pv.ParametricMobius(radius=param_a)
        elif surface == "Superquadric":
            mesh = pv.ParametricSuperquadric(
                xradius=param_a, yradius=param_b, zradius=param_c,
                n1=param_b, n2=param_c,
            )
        elif surface == "Ellipsoid":
            mesh = pv.ParametricEllipsoid(xradius=param_a, yradius=param_b, zradius=param_c)
        elif surface == "Boy Surface":
            mesh = pv.ParametricBoy()
        elif surface == "Dini Surface":
            mesh = pv.ParametricDini(a=param_a, b=param_b)
        elif surface == "Enneper":
            mesh = pv.ParametricEnneper()
        elif surface == "Roman Surface":
            mesh = pv.ParametricRoman(radius=param_a)
        elif surface == "Super Toroid":
            mesh = pv.ParametricSuperToroid(
                ringradius=param_a, crosssectionradius=param_b,
                n1=param_c, n2=param_c,
            )
        else:
            raise ValueError(f"Unknown surface: {surface}")

        info = f"{surface}: {mesh.n_points:,} points, {mesh.n_cells:,} cells"
        return IO.NodeOutput(mesh, info, ui={"text": [info]})
