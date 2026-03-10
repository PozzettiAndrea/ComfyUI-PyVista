# ComfyUI-PyVista

Geometry processing nodes powered by PyVista + meshio.

## Trame Preview

The **Preview PyVista** node uses a trame server for interactive 3D visualization with PyVista's native Vuetify3 toolbar (camera presets, edge toggle, grid, outline, axis, screenshot, export).

**Port requirement**: The trame websocket server runs on **port 8189** alongside ComfyUI on port 8188. Even though rendering is client-side (VTK.js in browser), the websocket is needed to push the serialized scene data. Make sure port 8189 is accessible from your browser (firewall, SSH tunnel, etc.).

If trame is unavailable or fails, the node falls back to the static VTK.js viewer automatically.
