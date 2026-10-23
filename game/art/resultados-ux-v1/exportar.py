"""Compatibility entry point for the shared Portuguese 96-glyph font exporter."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from build_text_font import main

if __name__ == '__main__':
    main()
