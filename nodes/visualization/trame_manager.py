"""Trame server lifecycle manager for ComfyUI-PyVista Preview nodes.

Manages a single shared trame server (client-mode, PyVistaLocalView)
with per-node namespaces for independent 3D views.

The trame server runs internally on 127.0.0.1 and is reverse-proxied
through ComfyUI's aiohttp server at /trame/ so it works through
Cloudflare tunnels and other proxied environments.
"""

from __future__ import annotations

import asyncio
import logging

# Silence extremely verbose trame internal loggers (they log every token/key at INFO level)
for _logger_name in [
    "trame_server.utils.namespace",
    "trame_server.state",
    "trame_server.controller",
    "trame_client.widgets.core",
    "wslink.backends.aiohttp",
    "wslink",
    "aiohttp.access",
    "aiohttp.server",
    "aiohttp.web",
]:
    logging.getLogger(_logger_name).setLevel(logging.WARNING)
import threading
from typing import Optional

import aiohttp
import aiohttp.web as web
import pyvista as pv

log = logging.getLogger("comfyui-pyvista")

# ---------------------------------------------------------------------------
# Legacy camera bridge JS (no longer used — bridge now runs in parent frame)
# ---------------------------------------------------------------------------
CAMERA_BRIDGE_JS = r"""
(function() {
    var REF_NAME = "__REF_NAME__";
    var NODE_ID = "__NODE_ID__";
    var POLL_MS = 500;
    var MAX_WAIT = 15000;
    var startTime = Date.now();
    var component = null;

    // Trame UI settings to sync back to parent for workflow persistence
    var SETTINGS = ['edge_visibility', 'outline_visibility', 'grid_visibility',
                    'axis_visibility', 'parallel_projection'];

    function init() {
        var appEl = document.querySelector('#app');
        if (!appEl || !appEl.__vue_app__) {
            if (Date.now() - startTime < MAX_WAIT) setTimeout(init, POLL_MS);
            return;
        }
        var vm = appEl.__vue_app__._instance;
        component = vm && vm.proxy && vm.proxy.$refs && vm.proxy.$refs[REF_NAME];
        if (!component || !component.getCamera) {
            if (Date.now() - startTime < MAX_WAIT) setTimeout(init, POLL_MS);
            return;
        }

        // Discover the trame state namespace prefix (e.g. "P_0x..._0_")
        var state = vm.proxy;
        var prefix = '';
        for (var key in state) {
            if (key.endsWith('_edge_visibility')) {
                prefix = key.replace('edge_visibility', '');
                break;
            }
        }

        // Hook canvas interaction events to capture camera state
        var canvas = document.querySelector('canvas');
        if (canvas) {
            var timer = null;
            var sendCamera = function() {
                try {
                    var cam = component.getCamera();
                    if (cam) {
                        var val = JSON.stringify(cam);
                        window.parent.postMessage(
                            { type: 'WIDGET_UPDATE', widget: 'camera_position', value: val },
                            '*'
                        );
                        // Also save to server for cross-execution persistence
                        fetch('/trame/api/save_camera', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ node_id: NODE_ID, camera_position: cam })
                        }).catch(function() {});
                    }
                } catch(e) { console.warn('[CameraBridge] sendCamera error:', e); }
            };
            canvas.addEventListener('mouseup', function() { clearTimeout(timer); timer = setTimeout(sendCamera, 200); });
            canvas.addEventListener('wheel', function() { clearTimeout(timer); timer = setTimeout(sendCamera, 200); });
            canvas.addEventListener('touchend', function() { clearTimeout(timer); timer = setTimeout(sendCamera, 200); });
        }

        // Poll trame state for UI setting changes and sync to parent
        if (prefix) {
            var lastSettings = {};
            setInterval(function() {
                SETTINGS.forEach(function(name) {
                    var val = state[prefix + name];
                    if (val !== lastSettings[name]) {
                        lastSettings[name] = val;
                        window.parent.postMessage(
                            { type: 'WIDGET_UPDATE', widget: name, value: val }, '*'
                        );
                    }
                });
            }, 500);
        }

        // Listen for camera restore from parent
        window.addEventListener('message', function(event) {
            if (event.data && event.data.type === 'RESTORE_CAMERA' && event.data.camera) {
                try {
                    var cam = typeof event.data.camera === 'string'
                        ? JSON.parse(event.data.camera) : event.data.camera;
                    component.setCamera(cam);
                } catch(e) { console.warn('[CameraBridge] Restore failed:', e); }
            }
            // Restore trame UI settings from parent
            if (event.data && event.data.type === 'RESTORE_SETTINGS' && event.data.settings && prefix) {
                var s = event.data.settings;
                SETTINGS.forEach(function(name) {
                    if (s[name] !== undefined) {
                        state[prefix + name] = s[name];
                    }
                });
            }
        });

        // Signal readiness to parent
        window.parent.postMessage({ type: 'CAMERA_BRIDGE_READY' }, '*');
        console.log('[CameraBridge] Initialized for ref=' + REF_NAME + (prefix ? ', prefix=' + prefix : ', no prefix found'));
    }

    setTimeout(init, 1000);
})();
"""

# ---------------------------------------------------------------------------
# Singleton state
# ---------------------------------------------------------------------------
_server = None
_server_lock = threading.Lock()
_server_ready = threading.Event()
_views: dict[str, dict] = {}          # node_id -> {plotter, viewer, view}
_saved_camera: dict[str, list] = {}   # node_id -> camera_position (preserved across re-executions)
_event_loop: Optional[asyncio.AbstractEventLoop] = None
_proxy_installed = False
_trame_port = 8189


def configure(port: int = 8189):
    """Set trame internal port before first use."""
    global _trame_port
    _trame_port = port


def set_event_loop(loop: asyncio.AbstractEventLoop):
    """Store ComfyUI's asyncio event loop (called from on_load)."""
    global _event_loop
    _event_loop = loop


# ---------------------------------------------------------------------------
# Reverse proxy: /trame/* -> 127.0.0.1:{_trame_port}/*
# ---------------------------------------------------------------------------

def setup_proxy(comfyui_app: web.Application):
    """Add reverse proxy routes on ComfyUI's aiohttp app.

    /trame/ws  -> WebSocket proxy to internal trame server
    /trame/{path}  -> HTTP proxy to internal trame server
    /trame/  -> redirect to index.html
    """
    global _proxy_installed
    if _proxy_installed:
        return
    _proxy_installed = True

    async def proxy_ws(request: web.Request) -> web.WebSocketResponse:
        """Proxy WebSocket connections to the internal trame server."""
        ws_server = web.WebSocketResponse(max_msg_size=8 * 1024 * 1024)
        await ws_server.prepare(request)

        trame_url = f"http://127.0.0.1:{_trame_port}/ws"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(trame_url, max_msg_size=8 * 1024 * 1024) as ws_client:

                    async def client_to_server():
                        async for msg in ws_server:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                await ws_client.send_str(msg.data)
                            elif msg.type == aiohttp.WSMsgType.BINARY:
                                await ws_client.send_bytes(msg.data)
                            elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.ERROR):
                                break

                    async def server_to_client():
                        async for msg in ws_client:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                await ws_server.send_str(msg.data)
                            elif msg.type == aiohttp.WSMsgType.BINARY:
                                await ws_server.send_bytes(msg.data)
                            elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.ERROR):
                                break

                    await asyncio.gather(
                        client_to_server(),
                        server_to_client(),
                        return_exceptions=True,
                    )
        except (aiohttp.ClientConnectorError, OSError) as e:
            log.warning("WebSocket proxy failed to connect to trame: %s", e)
            await ws_server.close()

        return ws_server

    async def proxy_http(request: web.Request) -> web.Response:
        """Proxy HTTP requests to the internal trame server."""
        path = request.match_info.get("path", "")
        url = f"http://127.0.0.1:{_trame_port}/{path}"
        if request.query_string:
            url += f"?{request.query_string}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    request.method, url,
                    headers={k: v for k, v in request.headers.items()
                             if k.lower() not in ("host", "transfer-encoding")},
                    data=await request.read(),
                ) as resp:
                    body = await resp.read()
                    # Forward headers, excluding hop-by-hop and content-type
                    # (content-type is set separately to avoid conflict)
                    headers = {
                        k: v for k, v in resp.headers.items()
                        if k.lower() not in (
                            "transfer-encoding", "content-encoding",
                            "content-type", "content-length",
                        )
                    }
                    return web.Response(
                        body=body,
                        status=resp.status,
                        headers=headers,
                        content_type=resp.content_type or "application/octet-stream",
                    )
        except aiohttp.ClientConnectorError:
            return web.Response(
                text="<html><body style='background:#1e1e1e;color:#888;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:sans-serif'>"
                     "<div style='text-align:center'><p>Trame server starting...</p><p style='font-size:0.8em'>Run a workflow to initialize the viewer.</p></div>"
                     "</body></html>",
                status=503,
                content_type="text/html",
            )

    async def save_camera_api(request: web.Request) -> web.Response:
        """API endpoint for client to save camera state back to server."""
        try:
            data = await request.json()
            node_id = data.get("node_id")
            camera = data.get("camera_position")
            if node_id and camera:
                save_camera(node_id, camera)
                return web.json_response({"status": "ok"})
            return web.json_response({"error": "missing node_id or camera_position"}, status=400)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def proxy_paraview(request: web.Request) -> web.Response:
        """Proxy the wslink session launcher endpoint (/paraview/).

        Trame's client JS constructs this URL from document.baseURI.
        In some environments (Cloudflare tunnels, iframes), the base URI
        may resolve to the root instead of /trame/, so we handle both
        /paraview/ and /trame/paraview/ (via the catch-all).
        """
        url = f"http://127.0.0.1:{_trame_port}/paraview/"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    request.method, url,
                    headers={k: v for k, v in request.headers.items()
                             if k.lower() not in ("host", "transfer-encoding")},
                    data=await request.read(),
                ) as resp:
                    body = await resp.read()
                    headers = {
                        k: v for k, v in resp.headers.items()
                        if k.lower() not in (
                            "transfer-encoding", "content-encoding",
                            "content-type", "content-length",
                        )
                    }
                    return web.Response(
                        body=body,
                        status=resp.status,
                        headers=headers,
                        content_type=resp.content_type or "application/octet-stream",
                    )
        except aiohttp.ClientConnectorError:
            return web.json_response(
                {"error": "Trame server not running"},
                status=503,
            )

    async def proxy_trame_ws(request: web.Request) -> web.WebSocketResponse:
        """Proxy WebSocket at /trame/ws to internal trame server /ws."""
        return await proxy_ws(request)

    # Camera save API (before catch-all)
    comfyui_app.router.add_post("/trame/api/save_camera", save_camera_api)
    # Wslink session launcher — browser may POST to /paraview/ (root)
    # due to baseURI resolution in iframes/tunnels
    comfyui_app.router.add_route("*", "/paraview/{path:.*}", proxy_paraview)
    comfyui_app.router.add_route("POST", "/paraview/", proxy_paraview)
    # WebSocket must be registered before the catch-all
    comfyui_app.router.add_get("/trame/ws", proxy_trame_ws)
    comfyui_app.router.add_route("*", "/trame/{path:.*}", proxy_http)
    log.debug("Trame reverse proxy installed at /trame/")


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

def _ensure_server():
    """Get or lazily create the shared trame server. Thread-safe."""
    global _server

    with _server_lock:
        if _server is not None:
            return _server

        from trame.app import get_server
        from trame.widgets import html as html_widgets
        from trame.widgets import vtk as vtk_widgets
        from trame.widgets import vuetify3 as vuetify3_widgets

        _server = get_server("comfyui-pyvista", client_type="vue3")
        html_widgets.initialize(_server)
        vtk_widgets.initialize(_server)
        vuetify3_widgets.initialize(_server)

        return _server


def _start_server_if_needed():
    """Start the trame server if not already running (must be on asyncio loop)."""
    server = _ensure_server()

    if server._running_stage == 0:
        def on_ready(**_):
            log.debug("Trame server ready on internal port %d", _trame_port)
            _server_ready.set()

        server.controller.on_server_ready.add(on_ready)
        server.start(
            exec_mode="task",
            host="127.0.0.1",  # Internal only — accessed via reverse proxy
            port=_trame_port,
            open_browser=False,
            show_connection_info=False,
            disable_logging=True,
            timeout=0,
            backend="aiohttp",
        )


async def _async_start_server():
    """Coroutine wrapper for starting the server."""
    _start_server_if_needed()
    await asyncio.sleep(0.2)


def _ensure_server_from_worker():
    """Start trame server from worker thread (blocks until ready)."""
    if _server is not None and _server_ready.is_set():
        return

    if _event_loop is None:
        raise RuntimeError("Event loop not set — was on_load() called?")

    future = asyncio.run_coroutine_threadsafe(_async_start_server(), _event_loop)
    future.result(timeout=30)
    _server_ready.wait(timeout=30)


# ---------------------------------------------------------------------------
# View management
# ---------------------------------------------------------------------------

def save_camera(node_id: str, camera_position: list):
    """Save camera position for a node (called from client via API)."""
    _saved_camera[node_id] = camera_position
    log.debug("Saved camera for node %s", node_id)


def get_saved_camera(node_id: str) -> list | None:
    """Get saved camera position for a node."""
    return _saved_camera.get(node_id)


def cleanup_view(node_id: str):
    """Close and remove an existing view for the given node_id.

    Saves camera state from the plotter before closing so it can be
    restored when the view is recreated on re-execution.
    """
    if node_id not in _views:
        return
    view_info = _views.pop(node_id)
    try:
        plotter = view_info.get("plotter")
        if plotter is not None:
            # Only save plotter camera if no client-side camera was saved via API
            # (in client mode, the plotter camera is stale — never updated by browser interaction)
            if node_id not in _saved_camera:
                try:
                    _saved_camera[node_id] = list(plotter.camera_position)
                except Exception:
                    pass
            plotter.close()
    except Exception as e:
        log.warning("Error cleaning up view %s: %s", node_id, e)


def create_view(node_id: str, mesh: pv.DataSet, camera_position: list | None = None) -> str:
    """Create a trame PyVistaLocalView for the given mesh.

    Returns a relative URL (/trame/...) for iframe embedding.
    Called from worker thread during execute().

    Args:
        node_id: Unique node identifier.
        mesh: PyVista mesh to display.
        camera_position: Optional camera position [(pos), (focal), (viewup)]
            to restore from a previous session. If not provided, uses any
            server-side saved state from the previous view.
    """
    _ensure_server_from_worker()
    cleanup_view(node_id)

    server = _ensure_server()
    namespace = f"pv_{node_id}"

    # Create offscreen plotter
    pv.OFF_SCREEN = True
    plotter = pv.Plotter(off_screen=True)

    # Extract surface for display
    if isinstance(mesh, pv.PolyData):
        surf = mesh
    else:
        surf = mesh.extract_surface()

    # Add mesh with first available scalar field
    if len(surf.point_data) > 0:
        scalar_name = list(surf.point_data.keys())[0]
        plotter.add_mesh(surf, scalars=scalar_name, show_edges=False)
    elif len(surf.cell_data) > 0:
        scalar_name = list(surf.cell_data.keys())[0]
        plotter.add_mesh(surf, scalars=scalar_name, show_edges=False)
    else:
        plotter.add_mesh(surf, color="lightblue", show_edges=False)

    # Restore camera from: explicit param > saved state > default
    cam = camera_position or _saved_camera.get(node_id)
    if cam:
        try:
            plotter.camera_position = cam
        except Exception:
            plotter.reset_camera()
    else:
        plotter.reset_camera()

    # Build trame view using PyVista's built-in trame UI
    from pyvista.trame.ui import get_viewer
    viewer = get_viewer(plotter, server=server, suppress_rendering=True)

    with viewer.make_layout(server, template_name=namespace) as layout:
        viewer.layout = layout
        view = viewer.ui(
            mode="client",
            default_server_rendering=False,
            collapse_menu=False,
        )

    _views[node_id] = {
        "plotter": None,
        "viewer": viewer,
        "view": view,
    }
    plotter.close()

    # Relative URL — goes through ComfyUI's reverse proxy at /trame/
    url = f"/trame/index.html?ui={namespace}&reconnect=auto"
    log.debug("Created trame view for node %s: %s", node_id, url)
    return url


def create_view_from_plotter(node_id: str, plotter: pv.Plotter) -> str:
    """Create a trame view from a pre-built plotter (with meshes already added).

    Returns a relative URL (/trame/...) for iframe embedding.
    Called from worker thread during execute().
    """
    _ensure_server_from_worker()
    cleanup_view(node_id)

    server = _ensure_server()
    namespace = f"pv_{node_id}"

    # Restore camera if saved
    cam = _saved_camera.get(node_id)
    if cam:
        try:
            plotter.camera_position = cam
        except Exception:
            plotter.reset_camera()
    else:
        plotter.reset_camera()

    # Build trame view using PyVista's built-in trame UI
    from pyvista.trame.ui import get_viewer
    viewer = get_viewer(plotter, server=server, suppress_rendering=True)

    with viewer.make_layout(server, template_name=namespace) as layout:
        viewer.layout = layout
        view = viewer.ui(
            mode="client",
            default_server_rendering=False,
            collapse_menu=False,
        )

    _views[node_id] = {
        "plotter": None,
        "viewer": viewer,
        "view": view,
    }
    plotter.close()

    url = f"/trame/index.html?ui={namespace}&reconnect=auto"
    log.debug("Created trame view (from plotter) for node %s: %s", node_id, url)
    return url
