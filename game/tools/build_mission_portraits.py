"""Pack original-source small-enemy portraits and preserve the other native icons.

Prepack 32x32 portraits so paging needs only one small DMA. Large enemies and
training targets retain their previous art; combat resources are read-only.
"""
from pathlib import Path
import argparse
import re
import struct

from PIL import Image

GAME = Path(__file__).resolve().parents[1]
TYPES = ('sq_red', 'sq_yellow', 'sq_purple', 'sq_orange',
         'tri_red', 'tri_yellow', 'tri_purple', 'tri_orange',
         'pen_red', 'pen_yellow', 'pen_purple', 'pen_orange',
         'dummy', 'target', 'boss')
SOURCE_PORTRAITS = ('sq_red', 'sq_yellow', 'sq_orange',
                   'tri_red', 'tri_yellow', 'tri_purple', 'tri_orange',
                   'pen_red', 'pen_yellow', 'pen_orange')
ART = GAME / 'art/mission-portraits-v3/portraits'


def portrait_pixels(kind, palette):
    """PNG indices are the existing insect CRAM indices, including transparent 0."""
    with Image.open(ART / f'{kind}.png') as image:
        assert image.mode == 'P' and image.size == (32, 32), kind
        assert image.info.get('transparency') == 0, kind
        assert image.getpalette()[:48] == palette, (kind, 'insect palette changed')
        pixels = list(image.tobytes())
    assert all(0 <= color < 16 for color in pixels), kind
    assert all(pixels[y*32+x] == 0 for y in range(32) for x in range(32)
               if x in (0, 31) or y in (0, 31)), (kind, 'clipped silhouette')
    return pixels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    icons = (GAME / 'res/insects/icons.bin').read_bytes()
    assert len(icons) == len(TYPES) * 512
    words = struct.unpack('>16H', (GAME / 'res/insects/palette.bin').read_bytes())
    palette = [((word >> shift) & 7)*255//7 for word in words for shift in (1, 5, 9)]
    portraits = bytearray()
    for index, kind in enumerate(TYPES):
        definition = (GAME / f'src/enemies/defs/{kind}.c').read_text()
        size = min(32, int(re.search(r'\.size\s*=\s*(\d+)', definition)[1]))
        assert size in (16, 24, 32), (kind, size)
        source = icons[index*512:(index+1)*512]
        pixels = portrait_pixels(kind, palette) if kind in SOURCE_PORTRAITS else None
        target = bytearray(512)
        for y in range(32):
            for x in range(32):
                if pixels is not None:
                    color = pixels[y*32+x]
                else:
                    sx, sy = x*size//32, y*size//32
                    src = (sx//8*(size//8)+sy//8)*32+(sy%8)*4+(sx%8)//2
                    color = (source[src] >> (0 if sx%2 else 4)) & 15
                dst = (x//8*4+y//8)*32+(y%8)*4+(x%8)//2
                target[dst] |= color << (0 if x%2 else 4)
        if size == 32:
            assert target == source
        portraits.extend(target)
    outputs = {
        GAME / 'res/mission/portraits.bin': portraits,
        GAME / 'res/mission_art.res': b'// 32x32 portraits from original corrected enemy art; large enemies and training targets retained.\nBIN mission_portraits "mission/portraits.bin" 4\n',
    }
    for path, data in outputs.items():
        if args.check:
            assert path.read_bytes() == data, path
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f'Mission: {len(TYPES)} 32x32 portraits ({len(SOURCE_PORTRAITS)} from original sources), {len(portraits)} ROM bytes; original insect palette.')


if __name__ == '__main__':
    main()
