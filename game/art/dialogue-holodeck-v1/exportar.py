"""Convert the selected console concept to native tiles; keep original portraits/font.

Only the mechanical background is sampled from the approved concept. Native
opaque monitor geometry covers all generated text and portraits. Runtime draws
the existing Portuguese font and original portrait tiles in those empty slots.
"""
from pathlib import Path
import argparse
import json
import re
import struct
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]
# CRAM levels are integers 0..7; indices 13/15 are the runtime text colours.
LEVELS = [(0,0,0), (0,0,0), (0,0,1), (1,1,1), (2,1,0), (2,2,2),
          (3,2,1), (3,3,3), (4,2,0), (3,3,1), (5,3,1), (1,1,0),
          (6,4,1), (7,6,2), (5,5,3), (7,7,3)]
PAL = [tuple(round(c*255/7) for c in rgb) for rgb in LEVELS]


def geometry():
    source = Image.open(ROOT/'propostas/c-console-central-v2-interlocutor-escuro.png').convert('RGB')
    im = source.resize((320,224), Image.Resampling.NEAREST)
    # Reusable pieces of the selected industrial bezel at the native scale.
    horizontal = im.crop((40,32,72,40))
    vertical = im.crop((24,48,32,80))
    d = ImageDraw.Draw(im)
    def plate(x,y,w,h):
        d.rectangle((x,y,x+w-1,y+h-1), fill=PAL[1])
        for offset in range(0,w,8):
            bit = horizontal.crop((offset%32,0,offset%32+8,8))
            im.paste(bit,(x+offset,y)); im.paste(bit,(x+offset,y+h-8))
        for offset in range(8,h-8,8):
            bit = vertical.crop((0,offset%32,8,offset%32+8))
            im.paste(bit,(x,y+offset)); im.paste(bit,(x+w-8,y+offset))
        d.rectangle((x+7,y+7,x+w-8,y+h-8), outline=PAL[6])
        for xx in (x+3,x+w-5):
            for yy in (y+3,y+h-5):
                d.point((xx,yy), fill=PAL[12])
    plate(8,8,304,24)
    plate(8,32,304,96)
    # Hide the concept's waveform between the native portrait consoles.
    d.rectangle((152,136,167,199), fill=PAL[3])
    for x in (155,164): d.line((x,136,x,199),fill=PAL[6])
    plate(8,136,144,64); plate(168,136,144,64)
    plate(8,200,304,24)
    # All real glyphs and both portraits are inserted by the runtime.
    return im


def resources():
    im = geometry()
    colours = {rgb: i for i,rgb in enumerate(PAL[1:],1)}
    def index(rgb):
        if rgb not in colours:
            colours[rgb] = min(range(1,16),key=lambda i:sum((a-b)**2 for a,b in zip(rgb,PAL[i])))
        return colours[rgb]
    tiles = [bytes(32)]; seen = {tiles[0]: 0}; grid = []
    for y in range(0,224,8):
        for x in range(0,320,8):
            pixels = [index(im.getpixel((x+dx,y+dy))) for dy in range(8) for dx in range(8)]
            tile = bytes(pixels[i]<<4|pixels[i+1] for i in range(0,64,2))
            if tile not in seen: seen[tile] = len(tiles); tiles.append(tile)
            grid.append(seen[tile])
    base_tiles = int(re.search(r'^#define NUM_TILES\s+(\d+)',
                              (GAME/'src/system/video/sprites/tiles.h').read_text(),re.M).group(1))
    assert 16+base_tiles+len(tiles)+144+400 <= 1440, 'Console must preserve base art and resident font'
    palette = struct.pack('>16H',*(r<<1|g<<5|b<<9 for r,g,b in LEVELS))
    return {GAME/'res/radio/tiles.bin': b''.join(tiles),
            GAME/'res/radio/map.bin': struct.pack('>1120H',*grid),
            GAME/'res/radio/palette.bin': palette}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    outputs = resources()
    for path,data in outputs.items():
        if args.check: assert path.read_bytes() == data, path
        else: path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
    print(json.dumps({'consoleTiles': len(outputs[GAME/'res/radio/tiles.bin'])//32,
                      'resolution': [320,224], 'portraitAnchors': [[16,144],[176,144]],
                      'dialogue': [24,56,26,4,16], 'portraitDimDivisor': 3}))


if __name__ == '__main__': main()
