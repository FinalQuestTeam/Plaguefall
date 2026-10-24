"""Compatibility entrypoint: phase3 now uses the whole-image scenery revision."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parents[1]/'campaign-whole-scenes-v1/validate_early.py'),run_name='__main__')
