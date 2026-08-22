"""ComfyUI-PyVista prestartup script -- seeds bundled assets into input/3d.

The viewer JavaScript is vendored under javascript/ and served from there;
it is no longer fetched from comfy-3d-viewers at startup.
"""

import shutil
from pathlib import Path

import folder_paths

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = SCRIPT_DIR / "assets"

# The CONFIGURED input directory, never the code-tree one: ComfyUI Desktop
# (--base-directory) and --input-directory both relocate it, and the load
# nodes only ever scan folder_paths.get_input_directory().
INPUT_DIR = Path(folder_paths.get_input_directory())


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


copy_assets()
