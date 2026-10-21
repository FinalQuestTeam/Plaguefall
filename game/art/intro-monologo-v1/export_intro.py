"""Pack the existing storyboard panels for the Mega Drive opening.

No new illustration: crop/resize, quantize whole tiles to two VDP palettes,
and export ROM-ready 4bpp tiles. Run --check to verify reproducibility.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import struct
import textwrap
import unicodedata
from functools import lru_cache

import numpy as np
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parent
GAME = ROOT.parents[1]
RES = GAME / "res/intro"
SOURCE = GAME / "art/storyboard-abertura-v1"
TW, TH = 42, 22
W, H = TW * 8, TH * 8
COUNT = TW * TH

# Existing panel interiors, excluding the ink gutters. The framing centers
# keep faces, prosthesis, cargo and radio legible in the 320x176 viewport.
SHOTS = [
    (1, (25, 70, 490, 484), (0.5, 0.65)),
    (1, (524, 70, 1064, 484), (0.5, 0.64)),
    (1, (1150, 28, 1509, 484), (0.5, 0.02)),
    (1, (76, 518, 527, 991), (0.5, 0.0)),
    (1, (556, 555, 996, 991), (0.5, 0.35)),
    (1, (1030, 555, 1507, 991), (0.5, 0.12)),
    (2, (15, 51, 577, 460), (0.5, 0.90)),
    (2, (599, 49, 1145, 460), (0.5, 0.50)),
    (2, (1220, 8, 1660, 460), (0.5, 0.0)),
    (2, (15, 526, 577, 931), (0.5, 0.10)),
    (2, (650, 487, 1150, 931), (0.5, 0.0)),
    (2, (1173, 523, 1660, 931), (0.5, 0.54)),
]

spec = importlib.util.spec_from_file_location("title_palette", GAME / "art/title-caatinga-v1/export_title.py")
title = importlib.util.module_from_spec(spec)
spec.loader.exec_module(title)


def balanced_lines(caption):
    """Keep the minimum line count, avoiding an isolated word on the last row."""
    count = len(textwrap.wrap(caption, width=36, break_long_words=False, break_on_hyphens=False))
    words = caption.split()
    target = (len(caption) - count + 1) / count
    @lru_cache(None)
    def layout(start, rows):
        if not rows:
            return (0, ()) if start == len(words) else (float("inf"), ())
        best = (float("inf"), ())
        for end in range(start + 1, len(words) + 1):
            line = " ".join(words[start:end])
            if len(line) > 36:
                break
            cost, rest = layout(end, rows - 1)
            candidate = (cost + (len(line) - target) ** 2, (line,) + rest)
            if candidate[0] < best[0]:
                best = candidate
        return best
    cost, result = layout(0, count)
    assert cost < float("inf") and " ".join(result) == caption
    return list(result)


def convert(image):
    pixels = np.asarray(image, dtype=np.int32)
    tiles = pixels.reshape(TH, 8, TW, 8, 3).transpose(0, 2, 1, 3, 4).reshape(COUNT, 64, 3)
    groups = (tiles.mean(axis=(1, 2)) > np.median(tiles.mean(axis=(1, 2)))).astype(int)
    for _ in range(6):
        palettes = [title.palette(tiles[groups == i]) for i in range(2)]
        distances = [((tiles[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(axis=3) for pal in palettes]
        costs = np.stack([d.min(axis=2).mean(axis=1) for d in distances], axis=1)
        chosen = costs.argmin(axis=1)
        if np.array_equal(chosen, groups):
            break
        groups = chosen
    indices = np.stack([d.argmin(axis=2) for d in distances])[chosen, np.arange(COUNT)]
    packed = ((indices[:, 0::2] << 4) | indices[:, 1::2]).astype(np.uint8).tobytes()
    hardware = [v for pal in palettes for v in title.words(pal)]
    rgb = np.stack(palettes)[chosen[:, None], indices]
    native = rgb.reshape(TH, TW, 8, 8, 3).transpose(0, 2, 1, 3, 4).reshape(H, W, 3)
    assert len(packed) == COUNT * 32 and all((v & 0x111) == 0 for v in hardware)
    return packed, chosen.astype(np.uint8).tobytes(), struct.pack(">32H", *hardware), Image.fromarray(native.astype(np.uint8))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    script = (GAME / "doc/historia/storyboard-abertura.md").read_text()
    speeches = re.findall(r'^\*\*(?:Damião(?:, em off)?|Comando, pelo rádio):\*\* “(.*?)”$', script, re.M)
    ranges = re.findall(r'^### \d{2} · .* · (\d\d):(\d\d)–(\d\d):(\d\d)$', script, re.M)
    durations = [int(c) * 60 + int(d) - int(a) * 60 - int(b) for a, b, c, d in ranges]
    assert len(speeches) == len(durations) == len(SHOTS) == 12 and sum(durations) == 89
    files = {}
    blobs = [bytearray(), bytearray(), bytearray()]
    previews, meta, declarations = [], [], []
    for i, (sheet, box, center) in enumerate(SHOTS):
        panel = Image.open(SOURCE / f"prancha-{sheet:02}.png").convert("RGB").crop(box)
        framed = ImageOps.fit(panel, (W, H), Image.Resampling.LANCZOS, centering=center)
        # A soft image-to-black edge replaces the old hard subtitle rectangle.
        pixels = np.asarray(framed, dtype=np.float32).copy()
        ramp = np.ones(H, dtype=np.float32)
        t = np.linspace(0.0, 1.0, 48)
        ramp[-48:] = 1.0 - t * t * (3.0 - 2.0 * t)
        pixels *= ramp[:, None, None]
        tiles, groups, palettes, image = convert(Image.fromarray(np.rint(pixels).astype(np.uint8)))
        for blob, data in zip(blobs, (tiles, groups, palettes)):
            blob.extend(data)
        caption = unicodedata.normalize("NFKD", speeches[i]).encode("ascii", "ignore").decode().upper()
        lines = balanced_lines(caption)
        assert len(lines) <= 4 and max(map(len, lines)) <= 36
        line_count = len(lines)
        total = sum(map(len, lines))
        lines += [""] * (4 - len(lines))
        line_literals = ", ".join(json.dumps(line) for line in lines)
        speaker = "COMANDO - RADIO" if i == 10 else "DAMIAO"
        declarations.append(f'    {{ {durations[i]}, {total}, {line_count}, {int(i == 10)}, {{ {line_literals} }} }},')
        first_y = 22 + (6 - line_count) // 2
        meta.append(dict(shot=i + 1, source_sheet=sheet, source_crop=box, crop_center=center, seconds=durations[i], fixed_crop=[8, 0], speaker=speaker, text=caption, lines=lines,
                         text_origins=[[(40-len(line))//2, first_y+row] for row,line in enumerate(lines[:line_count])]))
        previews.append(image)
        dest = ROOT / f"frames/{i+1:02}.png"
        if args.check:
            assert Image.open(dest).convert("RGB").tobytes() == image.tobytes(), dest
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            image.save(dest)
    for name, data in zip(("tiles", "groups", "palettes"), blobs):
        files[RES / f"{name}.bin"] = bytes(data)
    # Same SGDK glyphs, with an opaque black background during the opening.
    font = np.asarray(Image.open(GAME.parent / "SGDK/res/image/font_default.png"))
    assert font.shape == (48, 128)
    opaque = np.where(font == 0, 1, font).astype(np.uint8)
    font_tiles = opaque.reshape(6, 8, 16, 8).transpose(0, 2, 1, 3).reshape(96, 64)
    files[RES / "font.bin"] = ((font_tiles[:, 0::2] << 4) | font_tiles[:, 1::2]).astype(np.uint8).tobytes()
    header = '''// Generated by art/intro-monologo-v1/export_intro.py. Edit the storyboard text there.
#ifndef INTRO_SHOTS_H
#define INTRO_SHOTS_H
#define INTRO_SHOT_COUNT 12
#define INTRO_TILES_W 42
#define INTRO_TILES_H 22
#define INTRO_FRAME_TILES (INTRO_TILES_W * INTRO_TILES_H)
typedef struct {
    u8 seconds, letters, lineCount, radio;
    const char *lines[4];
} IntroShot;
static const IntroShot INTRO_SHOTS[INTRO_SHOT_COUNT] = {
''' + "\n".join(declarations) + '\n};\n#endif\n'
    files[GAME / "src/system/video/screens/intro_shots.h"] = header.encode()
    for path, data in files.items():
        if args.check:
            assert path.read_bytes() == data, path
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    report = dict(passed=True, image_size=[W, H], viewport=[320, 176], shots=12, seconds=sum(durations), frame_tiles=COUNT,
                  frame_vram_bytes=COUNT * 32, palettes_per_tile=1, palettes_per_shot=2, colors_per_palette=16,
                  caption_box=[36, 4], max_caption_rows=max(sum(bool(t) for t in m["lines"]) for m in meta),
                  animation="static framing + 0.4s palette fades + 12 dust/ember/soot sprites; no camera scroll or per-frame image uploads",
                  subtitle_layout="centered lines on black, soft 48px artwork edge, no speaker/counter/control labels",
                  files={str(p.relative_to(GAME)): dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest()) for p, data in files.items()}, scenes=meta)
    if not args.check:
        (ROOT / "export.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        contact = Image.new("RGB", (W * 3, (H + 24) * 4), (16, 16, 20))
        draw = ImageDraw.Draw(contact)
        for i, image in enumerate(previews):
            x, y = (i % 3) * W, (i // 3) * (H + 24)
            contact.paste(image, (x, y))
            draw.text((x + 8, y + H + 4), f"{i+1:02} / {durations[i]}s", fill="white")
        contact.save(ROOT / "contact-sheet.png")
    print(json.dumps({k: v for k, v in report.items() if k not in ("scenes", "files")}, indent=2))


if __name__ == "__main__":
    main()
