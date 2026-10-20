"""Technical PNG export of generated artwork; no drawing or pose synthesis.

Copies the untouched image_gen originals, extracts their ten supplied poses,
registers feet, downsamples with nearest neighbour, and maps to a fixed palette.
Run with Python + Pillow from any working directory.
"""

from pathlib import Path
from PIL import Image, ImageDraw
import hashlib
import json
import math
import shutil
from collections import deque

ROOT = Path(__file__).resolve().parent
LEVELS = [0, 36, 73, 109, 146, 182, 219, 255]


def spans(values):
    result = []
    start = None
    for x, value in enumerate(values + [False]):
        if value and start is None:
            start = x
        elif not value and start is not None:
            result.append([start, x])
            start = None
    return result


def extract_row(image, row, count):
    width, height = image.size
    y0, y1 = round(row * height / 2), round((row + 1) * height / 2)
    strip = image.crop((0, y0, width, y1))
    alpha = strip.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
    # Source poses can overlap in their horizontal projection (rifle vs. boot),
    # so split connected silhouettes in two dimensions instead of clipping cells.
    remaining = bytearray(alpha.tobytes())
    components = []
    for seed in range(len(remaining)):
        if not remaining[seed]:
            continue
        stack = [seed]
        remaining[seed] = 0
        pixels = []
        while stack:
            pos = stack.pop()
            pixels.append(pos)
            x, y = pos % width, pos // width
            for ny in range(max(0, y - 1), min(strip.height, y + 2)):
                for nx in range(max(0, x - 1), min(width, x + 2)):
                    other = ny * width + nx
                    if remaining[other]:
                        remaining[other] = 0
                        stack.append(other)
        xs, ys = [p % width for p in pixels], [p // width for p in pixels]
        components.append({"pixels": pixels, "box": [min(xs), min(ys), max(xs) + 1, max(ys) + 1]})
    components.sort(key=lambda c: len(c["pixels"]), reverse=True)
    primary = sorted(components[:count], key=lambda c: c["box"][0])
    if len(primary) != count or min(len(c["pixels"]) for c in primary) < 1000:
        raise ValueError(f"Row {row}: cannot identify {count} distinct complete source poses")
    groups = [[c] for c in primary]
    centers = [((c["box"][0] + c["box"][2]) / 2, (c["box"][1] + c["box"][3]) / 2) for c in primary]
    for component in components[count:]:
        if len(component["pixels"]) < 4:
            continue
        box = component["box"]
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        closest = min(range(count), key=lambda i: (cx - centers[i][0]) ** 2 + (cy - centers[i][1]) ** 2)
        groups[closest].append(component)
    frames = []
    source_bounds = []
    source_pixels = strip.load()
    for group in groups:
        bounds = (min(c["box"][0] for c in group), min(c["box"][1] for c in group),
                  max(c["box"][2] for c in group), max(c["box"][3] for c in group))
        frame = Image.new("RGBA", (bounds[2] - bounds[0], bounds[3] - bounds[1]))
        destination = frame.load()
        for component in group:
            for pos in component["pixels"]:
                x, y = pos % width, pos // width
                destination[x - bounds[0], y - bounds[1]] = source_pixels[x, y][:3] + (255,)
        frames.append(frame)
        source_bounds.append([bounds[0], bounds[1] + y0, bounds[2], bounds[3] + y0])
    return frames, source_bounds


def foot_center(image):
    mask = image.getchannel("A")
    band = mask.crop((0, max(0, image.height - max(2, round(image.height * .09))), image.width, image.height))
    box = band.getbbox()
    return (box[0] + box[2] - 1) / 2 if box else (image.width - 1) / 2


def indexed(image, colors):
    result = Image.new("P", image.size, 0)
    flat = [v for color in colors for v in color]
    result.putpalette(flat + [0] * (768 - len(flat)))
    cache = {}
    values = []
    for pixel in image.getdata():
        if pixel[3] < 128:
            values.append(0)
            continue
        rgb = pixel[:3]
        if rgb not in cache:
            cache[rgb] = min(range(1, 16), key=lambda i: sum((rgb[c] - colors[i][c]) ** 2 for c in range(3)))
        values.append(cache[rgb])
    result.putdata(values)
    result.info["transparency"] = 0
    return result


def export_enemy(enemy, colors):
    original = ROOT / "originals" / f"{enemy['id']}.png"
    if not original.exists():
        shutil.copy2(enemy["source"], original)
    source = Image.open(original).convert("RGBA")
    idle, bounds_idle = extract_row(source, 0, 4)
    run, bounds_run = extract_row(source, 1, 6)
    frames = idle + run
    # One geometric scale for all ten poses; never stretch a single pose.
    centers = [foot_center(frame) for frame in frames]
    scale = min(42 / max(f.height for f in frames), 30 / max(f.width for f in frames))
    sheet = Image.new("RGBA", (192, 96), (0, 0, 0, 0))
    registrations = []
    for i, (frame, center) in enumerate(zip(frames, centers)):
        row, col = (0, i) if i < 4 else (1, i - 4)
        size = (max(1, round(frame.width * scale)), max(1, round(frame.height * scale)))
        small = frame.resize(size, Image.Resampling.NEAREST)
        center_small = foot_center(small)
        x = min(31 - small.width, max(1, round(16 - center_small)))
        # Preserve idle foot stability. Suspension poses have deliberate lift.
        lift = [0, 0, 1, 3, 0, 1][col] if row else 0
        y = 47 - lift - small.height
        if not (0 <= x and x + small.width <= 32 and 0 <= y and y + small.height <= 48):
            raise ValueError(f"{enemy['id']}: pose exceeds its 32x48 cell")
        sheet.paste(small, (col * 32 + x, row * 48 + y))
        registrations.append({"row": row, "column": col, "feet_center_x": x + center_small,
                              "baseline_y": y + small.height - 1, "bounds": [x, y, x + size[0], y + size[1]]})
    final = indexed(sheet, colors)
    final.save(ROOT / "gfx" / f"{enemy['id']}.png", transparency=0, bits=4, optimize=False)
    final.convert("RGBA").resize((1152, 576), Image.Resampling.NEAREST).save(ROOT / "previews" / f"{enemy['id']}-6x.png")
    return {"id": enemy["id"], "source_size": list(source.size), "source_pose_bounds": bounds_idle + bounds_run,
            "uniform_downsample_scale": scale, "registration": registrations,
            "original_sha256": hashlib.sha256(original.read_bytes()).hexdigest()}


def previews(enemies):
    # Presentation previews are separate from every production spritesheet.
    board = Image.new("RGB", (800, 3 * 230), "#171b22")
    draw = ImageDraw.Draw(board)
    for i, enemy in enumerate(enemies):
        x, y = (i % 5) * 160, (i // 5) * 230
        sprite = Image.open(ROOT / "gfx" / f"{enemy['id']}.png").convert("RGBA").crop((0, 0, 32, 48))
        enlarged = sprite.resize((128, 192), Image.Resampling.NEAREST)
        board.paste(enlarged, (x + 16, y + 4), enlarged)
        draw.text((x + 12, y + 205), enemy["name"], fill="#dedbc8")
    board.save(ROOT / "previews" / "roster-4x.png")
    for state, length, duration in [("idle", 4, 180), ("run", 6, 100)]:
        animation = []
        row = 0 if state == "idle" else 1
        for phase in range(length):
            frame = Image.new("RGB", (800, 690), "#171b22")
            draw = ImageDraw.Draw(frame)
            for i, enemy in enumerate(enemies):
                x, y = (i % 5) * 160, (i // 5) * 230
                sheet = Image.open(ROOT / "gfx" / f"{enemy['id']}.png").convert("RGBA")
                sprite = sheet.crop((phase * 32, row * 48, (phase + 1) * 32, (row + 1) * 48))
                sprite = sprite.resize((128, 192), Image.Resampling.NEAREST)
                frame.paste(sprite, (x + 16, y + 4), sprite)
                draw.text((x + 12, y + 205), enemy["name"], fill="#dedbc8")
            animation.append(frame)
        animation[0].save(ROOT / "previews" / f"roster-{state}.gif", save_all=True,
                          append_images=animation[1:], duration=duration, loop=0, disposal=2)


def main():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    for folder in ["originals", "gfx", "previews", "validation"]:
        (ROOT / folder).mkdir(exist_ok=True)
    colors = [(0, 0, 0)] + [tuple(bytes.fromhex(s[1:])) for s in manifest["palette"][1:]]
    assert len(colors) == 16
    assert all(c in LEVELS for color in colors for c in color)
    reports = [export_enemy(enemy, colors) for enemy in manifest["enemies"]]
    previews(manifest["enemies"])
    palette = []
    for i, rgb in enumerate(colors):
        r, g, b = (LEVELS.index(c) * 2 for c in rgb)
        palette.append({"index": i, "rgb": list(rgb), "hex": "#" + bytes(rgb).hex().upper(),
                        "vdp": f"0x{(b << 8) | (g << 4) | r:03X}", "transparent": i == 0})
    (ROOT / "palette.json").write_text(json.dumps(palette, indent=2) + "\n")
    gpl = "GIMP Palette\nName: Darkspace MegaDrive shared\nColumns: 16\n# Index 0 transparent\n"
    gpl += "\n".join(f"{r:3} {g:3} {b:3}\tindex_{i}" for i, (r, g, b) in enumerate(colors)) + "\n"
    (ROOT / "palette.gpl").write_text(gpl)
    res = "// Orthographic camera: elevation 60 degrees above ground. Facing screen southeast.\n"
    res += "// Row 0: four idle frames; row 1: six run frames.\n"
    res += "\n".join(f'SPRITE enemy_{e["id"]} "gfx/{e["id"]}.png" 4 6 FAST 6 NONE BALANCED FAST' for e in manifest["enemies"]) + "\n"
    (ROOT / "enemies.res").write_text(res)
    (ROOT / "validation" / "export.json").write_text(json.dumps(reports, indent=2) + "\n")
    print(f"Exported {len(reports)} indexed sheets, palette, resource declarations and previews")


if __name__ == "__main__":
    main()
