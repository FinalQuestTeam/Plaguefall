"""Enlarge existing native insect icons for the mission cards, without new art.

Precompute nearest-neighbour 32x32 portraits so paging needs only one small
DMA, rather than scaling pixels while the Mega Drive display is disabled.
"""
from pathlib import Path
import argparse
import re

GAME = Path(__file__).resolve().parents[1]
TYPES = ('sq_red', 'sq_yellow', 'sq_purple', 'sq_orange',
         'tri_red', 'tri_yellow', 'tri_purple', 'tri_orange',
         'pen_red', 'pen_yellow', 'pen_purple', 'pen_orange',
         'dummy', 'target', 'boss')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    icons = (GAME / 'res/insects/icons.bin').read_bytes()
    assert len(icons) == len(TYPES) * 512
    portraits = bytearray()
    for index, kind in enumerate(TYPES):
        definition = (GAME / f'src/enemies/defs/{kind}.c').read_text()
        size = min(32, int(re.search(r'\.size\s*=\s*(\d+)', definition)[1]))
        assert size in (16, 24, 32), (kind, size)
        source = icons[index*512:(index+1)*512]
        target = bytearray(512)
        for y in range(32):
            for x in range(32):
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
        GAME / 'res/mission_art.res': b'// Native insect atlas, enlarged only for mission/guide portraits.\nBIN mission_portraits "mission/portraits.bin" 4\n',
    }
    for path, data in outputs.items():
        if args.check:
            assert path.read_bytes() == data, path
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f'Mission: {len(TYPES)} native 32x32 portraits, {len(portraits)} ROM bytes; original insect palette.')


if __name__ == '__main__':
    main()
