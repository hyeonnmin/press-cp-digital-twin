"""ASCII entry point for Kit's Windows locale-dependent dependency scanner."""
import importlib
from pathlib import Path
import sys

script_dir = str(Path(__file__).resolve().parent)
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
runtime = importlib.import_module("timeline_display")


class PressCpPlayBehavior(runtime.PressCpPlayBehavior):
    pass
