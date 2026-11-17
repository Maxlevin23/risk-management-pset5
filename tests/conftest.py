"""Shared test setup: make ``src/`` and the project root importable."""

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
for folder in (PROJECT_DIR, PROJECT_DIR / "src"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
