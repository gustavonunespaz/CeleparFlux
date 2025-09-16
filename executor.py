from __future__ import annotations

import sys
from pathlib import Path

PROJECT_SRC = Path(__file__).resolve().parent / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

from gptpar.interface.gui.main_window import launch_app  # noqa: E402  (import after sys.path manipulation)


if __name__ == "__main__":
    launch_app()
