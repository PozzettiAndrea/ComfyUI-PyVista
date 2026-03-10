"""ComfyUI-PyVista — geometry processing nodes powered by PyVista + meshio."""

import asyncio
import logging

from typing_extensions import override
from comfy_api.latest import ComfyExtension
from comfy_api.latest import io as IO

log = logging.getLogger("comfyui-pyvista")

# -- Import all node classes ------------------------------------------------
# IO (3)
from .nodes.io.load_meshio import LoadMeshio
from .nodes.io.save_meshio import SaveMeshio
from .nodes.io.convert import ConvertMesh
# Primitives (2)
from .nodes.primitives.create_primitive import CreatePrimitive
from .nodes.primitives.parametric_surface import CreateParametricSurface
# Analysis (4)
from .nodes.analysis.mesh_info import MeshInfo
from .nodes.analysis.curvature import ComputeCurvature
from .nodes.analysis.feature_edges import ExtractFeatureEdges
from .nodes.analysis.cell_quality import CellQuality
# Filters (8)
from .nodes.filters.clip import Clip
from .nodes.filters.slice import Slice
from .nodes.filters.threshold import Threshold
from .nodes.filters.decimate import Decimate
from .nodes.filters.smooth import Smooth
from .nodes.filters.subdivide import Subdivide
from .nodes.filters.clean import Clean
from .nodes.filters.contour import Contour
from .nodes.filters.compute_normals import ComputeNormals
# Boolean (1)
from .nodes.boolean.boolean import Boolean
# Geometry (3)
from .nodes.geometry.extrude import Extrude
from .nodes.geometry.delaunay import Delaunay
from .nodes.geometry.reconstruct_surface import ReconstructSurface
# Transforms (1)
from .nodes.transforms.transform import Transform
# Sampling (2)
from .nodes.sampling.sample_line import SampleOverLine
from .nodes.sampling.interpolate import Interpolate
# Spatial (2)
from .nodes.spatial.ray_trace import RayTrace
from .nodes.spatial.geodesic import Geodesic
# Connectivity (1)
from .nodes.connectivity.connectivity import Connectivity
# Deformation (1)
from .nodes.deformation.warp import Warp
# Voxel (1)
from .nodes.voxel.voxelize import Voxelize
# Visualization (4)
from .nodes.visualization.preview import PreviewPyVista
from .nodes.visualization.create_plotter import CreatePlotter
from .nodes.visualization.add_to_plotter import AddToPlotter
from .nodes.visualization.preview_plotter import PreviewPlotter


# -- Extension registration -------------------------------------------------
class PyVistaExtension(ComfyExtension):
    @override
    async def on_load(self) -> None:
        try:
            from .nodes.visualization import trame_manager
            loop = asyncio.get_event_loop()
            trame_manager.set_event_loop(loop)
            trame_manager.configure(port=8189)

            # Install reverse proxy on ComfyUI's aiohttp server
            # so trame is accessible at /trame/ through the same port
            from server import PromptServer
            trame_manager.setup_proxy(PromptServer.instance.app)

            log.debug("Trame manager initialized (internal port 8189, proxied at /trame/)")
        except ImportError as e:
            log.info("Trame not available — will use static VTK.js viewer: %s", e)
        except Exception as e:
            log.warning("Trame setup failed — will use static VTK.js viewer: %s", e)

    @override
    async def get_node_list(self) -> list[type[IO.ComfyNode]]:
        return [
            # IO
            LoadMeshio,
            SaveMeshio,
            ConvertMesh,
            # Primitives
            CreatePrimitive,
            CreateParametricSurface,
            # Analysis
            MeshInfo,
            ComputeCurvature,
            ExtractFeatureEdges,
            CellQuality,
            # Filters
            Clip,
            Slice,
            Threshold,
            Decimate,
            Smooth,
            Subdivide,
            Clean,
            Contour,
            ComputeNormals,
            # Boolean
            Boolean,
            # Geometry
            Extrude,
            Delaunay,
            ReconstructSurface,
            # Transforms
            Transform,
            # Sampling
            SampleOverLine,
            Interpolate,
            # Spatial
            RayTrace,
            Geodesic,
            # Connectivity
            Connectivity,
            # Deformation
            Warp,
            # Voxel
            Voxelize,
            # Visualization
            PreviewPyVista,
            CreatePlotter,
            AddToPlotter,
            PreviewPlotter,
        ]


async def comfy_entrypoint() -> PyVistaExtension:
    return PyVistaExtension()
