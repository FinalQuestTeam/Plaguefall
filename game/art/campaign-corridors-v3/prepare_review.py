"""Build the current corrected review; preserve historical evidence."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parent/"corrections/delivery-candidate/build_review.py"),run_name="__main__")
