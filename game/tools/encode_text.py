"""Encode UTF-8 C string literals after preprocessing, before compilation."""
import argparse
from pathlib import Path
from text_codec import encode_c

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(encode_c(args.source.read_text()), encoding='utf-8')
