"""Fit generated portrait artwork into native 32x32 indexed PNGs, without dithering.

The PNGs are editable production sources for tools/build_mission_portraits.py.
Only cropping, size conversion and the existing hardware palette are applied;
combat artwork and runtime palette resources are never written here.
"""
from pathlib import Path
import argparse
import json
import struct

from PIL import Image

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    words = struct.unpack('>16H', (GAME / 'res/insects/palette.bin').read_bytes())
    palette = [((word >> shift) & 7)*255//7 for word in words for shift in (1, 5, 9)]
    colors = [tuple(palette[i:i+3]) for i in range(0, 48, 3)]
    manifest = json.loads((ROOT / 'prompts.json').read_text())
    (ROOT / 'portraits').mkdir(exist_ok=True)
    for kind in manifest['assets']:
        source = Image.open(ROOT / 'source' / f'{kind}.png').convert('RGBA')
        alpha = source.getchannel('A').point(lambda a: 255 if a >= 128 else 0)
        bounds = alpha.getbbox()
        assert bounds, kind
        source = source.crop(bounds)
        source.thumbnail((30, 30), Image.Resampling.LANCZOS)
        portrait = Image.new('P', (32, 32), 0)
        portrait.putpalette(palette + [0]*(768-len(palette)))
        portrait.info['transparency'] = 0
        left, top = (32-source.width)//2, (32-source.height)//2
        for y in range(source.height):
            for x in range(source.width):
                r, g, b, a = source.getpixel((x, y))
                if a < 80:
                    continue
                # Index 10 is the card's brown backing. Keep it out of the
                # silhouette so thin antennae/legs do not blend into the card.
                index = min((i for i in range(1, 16) if i != 10), key=lambda i:
                            sum((v-c)**2 for v, c in zip((r, g, b), colors[i])))
                portrait.putpixel((left+x, top+y), index)
        output = ROOT / 'portraits' / f'{kind}.png'
        if args.check:
            with Image.open(output) as saved:
                assert saved.mode == 'P' and saved.size == (32, 32), kind
                assert saved.tobytes() == portrait.tobytes(), kind
                assert saved.getpalette() == portrait.getpalette(), kind
                assert saved.info.get('transparency') == 0, kind
        else:
            portrait.save(output, transparency=0, optimize=False)
        print(f'{kind}: {source.width}x{source.height} inside 32x32; native insect palette')


if __name__ == '__main__':
    main()
