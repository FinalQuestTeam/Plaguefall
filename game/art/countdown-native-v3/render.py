"""Countdown proposals composed from native game tiles and its original font.

Preview only: writes no runtime resources and does not build the ROM.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
import sys
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]
sys.path.insert(0, str(GAME / 'tools'))
from text_codec import encode

FONT_SOURCE = GAME / 'src/system/video/screens/result_font.h'
FONT = [int(n) for n in re.findall(r'\d+', FONT_SOURCE.read_text().split('= {', 1)[1].split('};', 1)[0])]
assert len(FONT) == 768
ROM = GAME / 'out/release/Plaguefall.bin'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def colour(word):
    return tuple(round(((word >> shift) & 7) * 255 / 7) for shift in (1, 5, 9))


def backing(name):
    folder = GAME / 'res' / name
    palette = [colour(c) for c in struct.unpack('>16H', (folder / 'palette.bin').read_bytes())]
    tiles = (folder / 'tiles.bin').read_bytes()
    mapping = struct.unpack('>1120H', (folder / 'map.bin').read_bytes())
    result = Image.new('RGB', (320, 224))
    pixels = result.load()
    for cell, tile in enumerate(mapping):
        assert tile * 32 + 32 <= len(tiles)
        x, y = (cell % 40) * 8, (cell // 40) * 8
        for py in range(8):
            for px in range(8):
                byte = tiles[tile * 32 + py * 4 + px // 2]
                pixels[x + px, y + py] = palette[(byte >> (4 if px % 2 == 0 else 0)) & 15]
    return result, palette


RADIO, RP = backing('radio')
PAPER, PP = backing('interface')


def text(im, value, x, y, ink, scale=1, centered=False):
    glyphs = encode(value)
    if centered:
        x -= len(glyphs) * 8 * scale // 2
    assert x >= 0 and x + len(glyphs) * 8 * scale <= 320, value
    assert 0 <= y <= 224 - 8 * scale, value
    draw = ImageDraw.Draw(im)
    for i, code in enumerate(glyphs):
        for row in range(8):
            bits = FONT[(code - 32) * 8 + row]
            for col in range(8):
                if bits & (128 >> col):
                    xx, yy = x + (i * 8 + col) * scale, y + row * scale
                    draw.rectangle((xx, yy, xx + scale - 1, yy + scale - 1), fill=ink)


def lamps(im, digit, y, center=160, on=None, off=None):
    draw = ImageDraw.Draw(im)
    for n in range(3):
        x = center - 24 + n * 20
        draw.rectangle((x, y, x + 7, y + 3), fill=on if n < digit else off)


def monitor(im, x, y, width, height):
    """Nine-slice of the actual conversation monitor; no replacement artwork."""
    source = RADIO.crop((8, 32, 312, 128))
    ImageDraw.Draw(im).rectangle((x, y, x + width - 1, y + height - 1), fill=RP[1])
    for xx in range(0, width, 8):
        sx = 0 if xx == 0 else 296 if xx == width - 8 else 8 + (xx - 8) % 288
        im.paste(source.crop((sx, 0, sx + 8, 8)), (x + xx, y))
        im.paste(source.crop((sx, 88, sx + 8, 96)), (x + xx, y + height - 8))
    for yy in range(8, height - 8, 8):
        sy = 8 + (yy - 8) % 80
        im.paste(source.crop((0, sy, 8, sy + 8)), (x, y + yy))
        im.paste(source.crop((296, sy, 304, sy + 8)), (x + width - 8, y + yy))


def model_one(digit):
    im = RADIO.copy()
    monitor(im, 8, 32, 304, 168)
    text(im, 'PREPARAÇÃO', 160, 16, RP[15], centered=True)
    text(im, 'PREPARE-SE', 160, 56, RP[15], centered=True)
    text(im, str(digit), 160, 80, RP[13], scale=8, centered=True)
    lamps(im, digit, 160, on=RP[13], off=RP[9])
    text(im, 'FASE 1', 24, 208, RP[15])
    text(im, 'PÁTIO DA IGREJA', 184, 208, RP[15])
    return im


def model_two(digit):
    im = PAPER.copy()
    text(im, 'PREPARAÇÃO', 16, 16, PP[12])
    text(im, 'FASE 1', 256, 16, PP[12])
    text(im, 'PÁTIO DA IGREJA', 16, 40, PP[12])
    text(im, 'PREPARE-SE', 160, 72, PP[12], centered=True)
    draw = ImageDraw.Draw(im)
    # Same rust strip used to select a menu action, with palette-native trim.
    draw.rectangle((104, 88, 215, 175), fill=PP[12])
    draw.line((104, 88, 215, 88), fill=PP[6])
    draw.line((104, 175, 215, 175), fill=PP[6])
    text(im, str(digit), 160, 96, PP[15], scale=7, centered=True)
    lamps(im, digit, 160, on=PP[15], off=PP[6])
    text(im, 'INÍCIO AUTOMÁTICO', 160, 208, PP[15], centered=True)
    return im


def portrait(im):
    source = (GAME / 'src/system/video/sprites/portraits_data.h').read_text()
    values = re.findall(r'0x[0-9A-Fa-f]+', source.split('PORTRAIT_PAL', 1)[1].split('};', 1)[0])
    palette = [colour(int(v, 16)) for v in values[:16]]
    rows = re.findall(r'"([0-9a-f]{48})"', source.split('PORTRAIT_ART', 1)[1])[:48]
    assert len(rows) == 48
    for y, row in enumerate(rows):
        for x, index in enumerate(row):
            im.putpixel((16 + x, 144 + y), palette[int(index, 16)])


def model_three(digit):
    im = RADIO.copy()
    text(im, 'PREPARAÇÃO DA MISSÃO', 160, 16, RP[15], centered=True)
    text(im, 'PREPARE-SE', 24, 40, RP[15])
    text(im, 'PÁTIO DA IGREJA', 24, 64, RP[13])
    text(im, 'FASE 1', 24, 88, RP[13])
    ImageDraw.Draw(im).line((208, 48, 208, 112), fill=RP[6])
    text(im, str(digit), 256, 48, RP[13], scale=6, centered=True)
    lamps(im, digit, 104, center=256, on=RP[13], off=RP[9])
    portrait(im)
    text(im, 'DAMIÃO', 72, 144, RP[15])
    text(im, 'PRONTO', 72, 160, RP[13])
    text(im, '>>>', 72, 184, RP[13])
    text(im, 'MISSÃO', 184, 144, RP[15])
    text(im, 'ELIMINE', 184, 160, RP[13])
    text(im, '10 INIMIGOS', 184, 176, RP[13])
    text(im, 'INÍCIO AUTOMÁTICO', 16, 208, RP[15])
    return im


def main():
    before = digest(ROM)
    entries = []
    for number, (name, render) in enumerate((('monitor-radio', model_one), ('cartao-missao', model_two), ('console-dividido', model_three)), 1):
        frames = [render(digit) for digit in (3, 2, 1)]
        prefix = f'{number:02d}-{name}'
        for digit, frame in zip((3, 2, 1), frames):
            frame.save(ROOT / f'{prefix}-{digit}-native.png')
        large = [frame.resize((960, 672), Image.Resampling.NEAREST) for frame in frames]
        large[0].save(ROOT / f'{prefix}.png')
        large[0].save(ROOT / f'{prefix}.gif', save_all=True, append_images=large[1:], duration=1000, loop=0, optimize=False, disposal=2)
        # Resample-free preview: every displayed native pixel is a 3x3 square.
        assert large[0].resize((320,224), Image.Resampling.NEAREST).tobytes() == frames[0].tobytes()
        entries.append({'id':number, 'name':name, 'image':f'{prefix}.png', 'animation':f'{prefix}.gif', 'resolution':[320,224], 'previewScale':3, 'digits':[3,2,1], 'millisecondsPerDigit':1000})
    assert digest(ROM) == before
    sources = [FONT_SOURCE, GAME/'res/radio/tiles.bin', GAME/'res/radio/map.bin', GAME/'res/radio/palette.bin', GAME/'res/interface/tiles.bin', GAME/'res/interface/map.bin', GAME/'res/interface/palette.bin', GAME/'src/system/video/sprites/portraits_data.h']
    report = {'status':'preview_only', 'romChanged':False, 'romSHA256':before, 'method':'native tile decoding, existing 8x8 font and existing portrait; no generated artwork', 'hardwareValidated':False, 'sources':{str(p.relative_to(GAME)):digest(p) for p in sources}, 'proposals':entries}
    (ROOT/'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'previews':len(entries),'digits':3,'romChanged':False},ensure_ascii=False))


if __name__ == '__main__':
    main()
