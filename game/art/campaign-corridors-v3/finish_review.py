"""Validate and publish the current hash-bound correction; no historical auto-approval."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parent/"corrections/delivery-candidate/publish_results.py"),run_name="__main__")
