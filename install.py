"""ComfyUI-PyVista install script — installs pip dependencies."""

import subprocess
import sys
from pathlib import Path

REQUIREMENTS = Path(__file__).resolve().parent / "requirements.txt"


def install():
    if REQUIREMENTS.exists():
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)],
        )


if __name__ == "__main__":
    install()
