"""Pack the approved storyboard into 14 images and 18 independently timed captions."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import textwrap
import unicodedata

import numpy as np
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]
STORY = GAME / 'art/storyboard-abertura-v2'
RES = GAME / 'res/intro'
W, H = 336, 176
COUNT = W // 8 * (H // 8)
spec = importlib.util.spec_from_file_location('intro_palette', GAME / 'art/intro-monologo-v1/export_intro.py')
palette = importlib.util.module_from_spec(spec)
spec.loader.exec_module(palette)


def normalized(text):
    return unicodedata.normalize('NFKD', text.replace('…', '...')).encode('ascii', 'ignore').decode().upper()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    storyboard = json.loads((STORY / 'storyboard.json').read_text())
    shots = storyboard['shots']
    files, scenes, shot_declarations, caption_declarations, previews = {}, [], [], [], []
    blobs = [bytearray(), bytearray(), bytearray()]
    caption_index = 0
    for index, shot in enumerate(shots):
        source = shot['source']
        path = (GAME / f'art/storyboard-abertura-v1/prancha-{source["sheet"]:02}.png'
                if 'sheet' in source else STORY / source['file'])
        panel = Image.open(path).convert('RGB')
        if 'box' in source:
            panel = panel.crop(tuple(source['box']))
        # Match the approved 320:176 viewport; invisible 8px guards must not
        # further crop the arm, civilians or the cleaned panel borders.
        visible = ImageOps.fit(panel, (320, H), Image.Resampling.LANCZOS, centering=tuple(source['center']))
        framed = Image.new('RGB', (W, H))
        framed.paste(visible, (8, 0))
        framed.paste(visible.crop((0, 0, 1, H)).resize((8, H)), (0, 0))
        framed.paste(visible.crop((319, 0, 320, H)).resize((8, H)), (328, 0))
        pixels = np.asarray(framed, dtype=np.float32).copy()
        ramp = np.ones(H, dtype=np.float32)
        t = np.linspace(0.0, 1.0, 48)
        ramp[-48:] = 1.0 - t * t * (3.0 - 2.0 * t)
        pixels *= ramp[:, None, None]
        tiles, groups, colors, image = palette.convert(Image.fromarray(np.rint(pixels).astype(np.uint8)))
        for blob, data in zip(blobs, (tiles, groups, colors)):
            blob.extend(data)
        captions = []
        start = 0
        for entry in shot['captions']:
            # Preserve the reviewed line breaks as well as the exact wording.
            caption = normalized(entry['text'])
            lines = textwrap.wrap(caption, width=36, break_long_words=False, break_on_hyphens=False)
            assert 1 <= len(lines) <= 4 and max(map(len, lines)) <= 36
            letters = sum(map(len, lines))
            assert entry['seconds'] - letters / 36 >= 1.5
            first_y = 22 + (6 - len(lines)) // 2
            radio = entry['speaker'].startswith('Comando')
            captions.append(dict(caption=caption_index + 1, start_seconds=start, seconds=entry['seconds'],
                                 speaker=entry['speaker'], text=caption, lines=lines,
                                 text_origins=[[(40-len(line))//2, first_y+row] for row, line in enumerate(lines)]))
            padded = lines + [''] * (4 - len(lines))
            caption_declarations.append('    { %d, %d, %d, %d, { %s } },' %
                (entry['seconds'], letters, len(lines), radio, ', '.join(json.dumps(line) for line in padded)))
            caption_index += 1
            start += entry['seconds']
        first = caption_index - len(captions)
        shot_declarations.append(f'    {{ {start}, {first}, {len(captions)} }},')
        # Keep last-caption fields for old tooling, with all captions explicit.
        scenes.append(dict(shot=index+1, title=shot['title'], seconds=start, source=str(path.relative_to(GAME)),
                           source_crop=source.get('box'), crop_center=source['center'], fixed_crop=[8, 0],
                           captions=captions, **{key: captions[-1][key] for key in ('speaker', 'text', 'lines', 'text_origins')}))
        previews.append(image)
        dest = ROOT / f'frames/{index+1:02}.png'
        if args.check:
            assert Image.open(dest).convert('RGB').tobytes() == image.tobytes(), dest
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            image.save(dest)
    assert len(shots) == 14 and caption_index == 18 and sum(s['seconds'] for s in scenes) == 101
    for name, blob in zip(('tiles', 'groups', 'palettes'), blobs):
        files[RES / f'{name}.bin'] = bytes(blob)
    font = np.asarray(Image.open(GAME.parent / 'SGDK/res/image/font_default.png'))
    opaque = np.where(font == 0, 1, font).astype(np.uint8)
    font_tiles = opaque.reshape(6, 8, 16, 8).transpose(0, 2, 1, 3).reshape(96, 64)
    files[RES / 'font.bin'] = ((font_tiles[:, 0::2] << 4) | font_tiles[:, 1::2]).astype(np.uint8).tobytes()
    header = '''// Generated by art/intro-monologo-v2/export_intro.py from the approved storyboard JSON.
#ifndef INTRO_SHOTS_H
#define INTRO_SHOTS_H
#define INTRO_SHOT_COUNT 14
#define INTRO_CAPTION_COUNT 18
#define INTRO_DURATION_SECONDS 101
#define INTRO_TILES_W 42
#define INTRO_TILES_H 22
#define INTRO_FRAME_TILES (INTRO_TILES_W * INTRO_TILES_H)
typedef struct {
    u8 seconds, letters, lineCount, radio;
    const char *lines[4];
} IntroCaption;
typedef struct {
    u8 seconds, firstCaption, captionCount;
} IntroShot;
static const IntroCaption INTRO_CAPTIONS[INTRO_CAPTION_COUNT] = {
''' + '\n'.join(caption_declarations) + '''
};
static const IntroShot INTRO_SHOTS[INTRO_SHOT_COUNT] = {
''' + '\n'.join(shot_declarations) + '\n};\n#endif\n'
    files[GAME / 'src/system/video/screens/intro_shots.h'] = header.encode()
    files[GAME / 'res/intro_data.res'] = b'''// Approved opening: 14 images, each 336x176, with 18 timed captions.
BIN intro_tiles "intro/tiles.bin" 4
BIN intro_groups "intro/groups.bin" 2
BIN intro_palettes "intro/palettes.bin" 2
BIN intro_font "intro/font.bin" 4
'''
    for path, data in files.items():
        if args.check:
            assert path.read_bytes() == data, path
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    report = dict(passed=True, storyboard='art/storyboard-abertura-v2/storyboard.json', shots=14, captions=18,
                  seconds=101, image_size=[W, H], viewport=[320, 176], frame_tiles=COUNT,
                  frame_vram_bytes=COUNT*32, palettes_per_shot=2, caption_box=[36, 4],
                  scenes=scenes, files={str(p.relative_to(GAME)):dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest()) for p,data in files.items()})
    if not args.check:
        (ROOT / 'export.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
        board = Image.new('RGB', (W*3, (H+24)*5), (16,16,20))
        draw = ImageDraw.Draw(board)
        for i, image in enumerate(previews):
            x,y = i%3*W, i//3*(H+24)
            board.paste(image, (x,y))
            draw.text((x+8,y+H+4), f'{i+1:02} / {scenes[i]["seconds"]}s', fill='white')
        board.save(ROOT / 'contact-sheet.png')
    print(json.dumps({key:value for key,value in report.items() if key not in ('scenes','files')}, indent=2))


if __name__ == '__main__':
    main()
