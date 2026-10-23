"""Export the selected single-monitor radio using the existing native artwork.

The first tiles are shared by mission pages and loading. Opaque native glyphs
and three small indicator patterns belong only to the loading WINDOW.
"""
from pathlib import Path
import argparse
import json
import re
import struct
import sys

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]
sys.path.insert(0, str(GAME/'tools'))
from text_codec import ACCENTS, encode


def resources():
    source = (GAME/'res/radio/tiles.bin').read_bytes()
    grid = list(struct.unpack('>1120H', (GAME/'res/radio/map.bin').read_bytes()))
    original = grid[:]
    black = original[5*40+2]
    for y in range(4,25):
        for x in range(1,39):
            grid[y*40+x] = black
    for x in range(1,39):
        grid[4*40+x] = original[4*40+x]
        grid[24*40+x] = original[15*40+x]
    for y in range(5,24):
        sy = 5+(y-5)%10
        grid[y*40+1] = original[sy*40+1]
        grid[y*40+38] = original[sy*40+38]
    tiles = []
    seen = {}
    def add(data):
        if data not in seen:
            seen[data] = len(tiles)
            tiles.append(data)
        return seen[data]
    def opaque(data):
        return bytes(((b>>4 or 1)<<4)|(b&15 or 1) for b in data)
    mapping = [add(opaque(source[t*32:t*32+32])) for t in grid]
    background_count = len(tiles)
    glyphs = [0]*96
    font_source = (GAME/'src/system/video/screens/result_font.h').read_text()
    font = [int(n) for n in re.findall(r'\d+',font_source.split('= {',1)[1].split('};',1)[0])]
    for char in encode(' -/0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'+ACCENTS):
        rows = font[(char-32)*8:(char-32)*8+8]
        pixels = [15 if bits&(128>>x) else 1 for bits in rows for x in range(8)]
        glyphs[char-32] = add(bytes(pixels[i]<<4|pixels[i+1] for i in range(0,64,2)))
    ink = add(bytes([0xdd])*32)
    lamp_on = add(bytes([0xdd])*16+bytes([0x11])*16)
    lamp_off = add(bytes([0x99])*16+bytes([0x11])*16)
    # Borrow only the low tile region; actors and scenery retain their layout.
    assert len(tiles)+2 < 240
    header = '#ifndef RADIO_PANEL_DATA_H\n#define RADIO_PANEL_DATA_H\n'
    for name,value in [('TILE_COUNT',background_count),('OVERLAY_COUNT',len(tiles)),('BLACK_TILE',seen[bytes([0x11])*32]),('INK_TILE',ink),('LAMP_ON_TILE',lamp_on),('LAMP_OFF_TILE',lamp_off)]:
        header += f'#define RADIO_PANEL_{name} {value}\n'
    header += 'static const u8 RADIO_PANEL_GLYPHS[96] = {\n'
    for i in range(0,96,16):
        header += '    '+','.join(map(str,glyphs[i:i+16]))+',\n'
    header += '};\n#endif\n'
    return {
        GAME/'res/radio_panel/tiles.bin':b''.join(tiles),
        GAME/'res/radio_panel/map.bin':struct.pack('>1120H',*mapping),
        GAME/'res/radio_panel/palette.bin':(GAME/'res/radio/palette.bin').read_bytes(),
        GAME/'res/radio_panel.res':b'// Shared native single-monitor radio; opaque loading glyphs follow background tiles.\nBIN radio_panel_tiles "radio_panel/tiles.bin" 4\nBIN radio_panel_map "radio_panel/map.bin" 2\nBIN radio_panel_palette "radio_panel/palette.bin" 2\n',
        GAME/'src/system/video/screens/radio_panel_data.h':header.encode(),
    },background_count,len(tiles)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    outputs,background,overlay=resources()
    for path,data in outputs.items():
        if args.check:
            assert path.read_bytes()==data,path
        else:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print(json.dumps({'backgroundTiles':background,'loadingTiles':overlay,'shadowBytes':overlay*32,'nativeEnemyArtModified':False}))


if __name__=='__main__':
    main()
