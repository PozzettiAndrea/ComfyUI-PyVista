"""ComfyUI-PyVista prestartup script — copies assets and viewer files."""

import logging
import shutil
from pathlib import Path

log = logging.getLogger("comfyui-pyvista")

SCRIPT_DIR = Path(__file__).resolve().parent
COMFYUI_DIR = SCRIPT_DIR.parent.parent
ASSETS_DIR = SCRIPT_DIR / "assets"
INPUT_DIR = COMFYUI_DIR / "input"


def copy_assets():
    if not ASSETS_DIR.exists():
        return
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = INPUT_DIR / "3d"
    dest.mkdir(exist_ok=True)
    for src_file in ASSETS_DIR.iterdir():
        if src_file.is_file():
            dst_file = dest / src_file.name
            if not dst_file.exists():
                shutil.copy2(src_file, dst_file)


def copy_viewers():
    """Copy VTK.js viewer infrastructure from comfy-3d-viewers."""
    try:
        from comfy_3d_viewers import copy_viewer
        copy_viewer("pyvista", SCRIPT_DIR / "web")
        copy_viewer("pyvista_text_report", SCRIPT_DIR / "web")
    except ImportError:
        log.warning("comfy-3d-viewers not installed, 3D preview will not work")
    except Exception as e:
        log.warning("Failed to copy viewer files: %s", e)


copy_assets()
copy_viewers()
